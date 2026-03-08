<script lang="ts">
  import { open, save } from '@tauri-apps/plugin-dialog';
  import { invoke } from '@tauri-apps/api/core';
  import { writable } from 'svelte/store';

  interface FileInfo {
    path: string;
    name: string;
    preview?: string;  // base64 image
    isLoading?: boolean;
  }

  interface PdfResponse {
    success: boolean;
    error?: string;
    output_path?: string;
    page_count?: number;
  }

  interface PreviewResponse {
    success: boolean;
    image?: string;  // base64 image
    error?: string;
  }
  const files = writable<FileInfo[]>([]);
  let isProcessing = $state(false);
  let progress = $state(0);
  let statusMessage = $state('');


  async function loadPreview(fileInfo: FileInfo): Promise<void> {
    try {
      fileInfo.isLoading = true;
      files.update(f => f); // Trigger reactivity

      const response = await invoke<PreviewResponse>('pdf_get_file_preview', {
        file: fileInfo.path,
        zoom: 0.3
      });

      if (response.success && response.image) {
        fileInfo.preview = `data:image/png;base64,${response.image}`;
      }
    } catch (err) {
      console.error('Failed to load preview:', err);
    } finally {
      fileInfo.isLoading = false;
      files.update(f => f); // Trigger reactivity
    }
  }

  async function selectFiles() {
    try {
      const selected = await open({
        multiple: true,
        filters: [{
          name: 'PDF',
          extensions: ['pdf']
        }]
      });

      if (selected && Array.isArray(selected)) {
        files.update(current => {
          const newFiles = [...current];
          for (const path of selected) {
            if (!newFiles.find(f => f.path === path)) {
              const fileInfo: FileInfo = {
                path,
                name: path.split(/[/\\]/).pop() || path,
                isLoading: true
              };
              newFiles.push(fileInfo);
              // Load preview asynchronously
              loadPreview(fileInfo);
            }
          }
          return newFiles;
        });
      }
    } catch (err) {
      console.error('Failed to select files:', err);
      statusMessage = `选择文件失败: ${err}`;
    }
  }

  function removeFile(index: number) {
    files.update(current => current.filter((_, i) => i !== index));
  }

  function moveUp(index: number) {
    if (index <= 0) return;
    files.update(current => {
      const newFiles = [...current];
      [newFiles[index - 1], newFiles[index]] = [newFiles[index], newFiles[index - 1]];
      return newFiles;
    });
  }

  function moveDown(index: number) {
    files.update(current => {
      if (index >= current.length - 1) return current;
      const newFiles = [...current];
      [newFiles[index], newFiles[index + 1]] = [newFiles[index + 1], newFiles[index]];
      return newFiles;
    });
  }

  function generateDefaultMergeName(): string {
    let currentFiles: FileInfo[] = [];
    files.subscribe(f => currentFiles = f)();
    
    if (currentFiles.length === 0) {
      return 'merged.pdf';
    }
    
    const firstName = currentFiles[0].name;
    const baseName = firstName.replace(/\.pdf$/i, '');
    return `${baseName}_merge.pdf`;
  }


  async function mergeFiles() {
    let currentFiles: FileInfo[] = [];
    files.subscribe(f => currentFiles = f)();

    if (currentFiles.length < 2) {
      statusMessage = '请至少选择2个PDF文件';
      return;
    }

    // 弹出保存对话框
    let outputPath: string | null = null;
    try {
      const selected = await save({
        filters: [{
          name: 'PDF',
          extensions: ['pdf']
        }],
        defaultPath: generateDefaultMergeName()
      });
      
      if (!selected || typeof selected !== 'string') {
        return; // 用户取消
      }
      outputPath = selected;
    } catch (err) {
      console.error('Failed to select output path:', err);
      statusMessage = `选择输出路径失败: ${err}`;
      return;
    }

    isProcessing = true;
    progress = 0;
    statusMessage = '正在合并PDF文件...';

    try {
      const filePaths = currentFiles.map(f => f.path);

      const response = await invoke<PdfResponse>('pdf_merge', {
        files: filePaths,
        output: outputPath
      });

      if (response.success) {
        progress = 100;
        statusMessage = `合并成功！共 ${response.page_count} 页`;
        files.set([]);
      } else {
        statusMessage = `合并失败: ${response.error || '未知错误'}`;
      }
    } catch (err) {
      console.error('Merge failed:', err);
      statusMessage = `合并失败: ${err}`;
    } finally {
      isProcessing = false;
      // Clear status message after 3 seconds
      setTimeout(() => {
        statusMessage = '';
        progress = 0;
      }, 3000);
    }
  }
</script>

<div class="p-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-800">PDF合并</h1>
    <p class="text-gray-600 mt-2">将多个PDF文件合并为一个</p>
  </div>
  
  <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-700">已选择的文件</h2>
      <button
        onclick={selectFiles}
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        添加PDF文件
      </button>
    </div>
    
    {#if $files.length === 0}
      <div class="text-center py-12 text-gray-400">
        <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2h-2m8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 00-2-2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
        </svg>
        <p>点击上方按钮添加PDF文件</p>
      </div>
    {:else}
      <ul class="space-y-2">
        {#each $files as file, index}
          <li
            class="flex items-center justify-between p-3 rounded-lg group bg-gray-50 hover:bg-gray-100"
          >
            <div class="flex items-center gap-3 flex-1 min-w-0">
              <span class="text-gray-400 font-mono text-sm w-8 shrink-0">{index + 1}</span>

              <!-- Preview thumbnail -->
              <div class="w-14 h-16 shrink-0 flex items-center justify-center bg-gray-200 rounded overflow-hidden">
                {#if file.isLoading}
                  <svg class="w-6 h-6 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                {:else if file.preview}
                  <img src={file.preview} alt="PDF预览" class="w-full h-full object-contain" />
                {:else}
                  <svg class="w-8 h-8 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A1 1 0 0112.293.707L13.293 2H12a1 1 0 01-1 1v1h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v3a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" clip-rule="evenodd" />
                  </svg>
                {/if}
              </div>

              <span class="flex-1 truncate text-gray-700" title={file.name}>{file.name}</span>
            </div>
            <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
              <!-- Move up/down buttons -->
              <button
                onclick={() => moveUp(index)}
                disabled={index === 0}
                class="p-1 text-gray-400 hover:text-blue-600 disabled:opacity-30 disabled:cursor-not-allowed"
                title="上移"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                </svg>
              </button>
              <button
                onclick={() => moveDown(index)}
                disabled={index === $files.length - 1}
                class="p-1 text-gray-400 hover:text-blue-600 disabled:opacity-30 disabled:cursor-not-allowed"
                title="下移"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div class="w-px h-5 bg-gray-300 mx-1"></div>
              <button
                onclick={() => removeFile(index)}
                class="p-1 text-gray-400 hover:text-red-600"
                title="删除"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
  

  <!-- Status message -->
  {#if statusMessage}
    <div class="mb-6 p-4 rounded-lg {isProcessing ? 'bg-blue-50 text-blue-700' : statusMessage.includes('成功') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}">
      <div class="flex items-center gap-2">
        {#if isProcessing}
          <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 9.373 0 012 4z"></path>
          </svg>
        {/if}
        <span>{statusMessage}</span>
      </div>
    </div>
  {/if}
  
  <!-- Progress bar -->
  {#if isProcessing}
    <div class="mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm text-gray-600">处理中...</span>
        <span class="text-sm text-gray-600">{progress}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div 
          class="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style="width: {progress}%"
        ></div>
      </div>
    </div>
  {/if}
  
  <div class="flex items-center gap-4">
    <button
      onclick={mergeFiles}
      disabled={$files.length < 2 || isProcessing}
      class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
      </svg>
      开始合并
    </button>
    <span class="text-sm text-gray-500">
      {$files.length} 个文件已选择
    </span>
  </div>
</div>
