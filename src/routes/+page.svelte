<script lang="ts">
  import { open, save } from '@tauri-apps/plugin-dialog';
  import { invoke } from '@tauri-apps/api/core';
  import { writable } from 'svelte/store';

  interface FileInfo {
    path: string;
    name: string;
  }

  const files = writable<FileInfo[]>([]);
  let isProcessing = false;
  let progress = 0;

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
              newFiles.push({
                path,
                name: path.split(/[/\\]/).pop() || path
              });
            }
          }
          return newFiles;
        });
      }
    } catch (err) {
      console.error('Failed to select files:', err);
    }
  }

  function removeFile(index: number) {
    files.update(current => current.filter((_, i) => i !== index));
  }

  function moveUp(index: number) {
    if (index > 0) {
      files.update(current => {
        const newFiles = [...current];
        [newFiles[index - 1], newFiles[index]] = [newFiles[index], newFiles[index - 1]];
        return newFiles;
      });
    }
  }

  function moveDown(index: number) {
    files.update(current => {
      if (index < current.length - 1) {
        const newFiles = [...current];
        [newFiles[index], newFiles[index + 1]] = [newFiles[index + 1], newFiles[index]];
        return newFiles;
      }
      return current;
    });
  }

  async function mergeFiles() {
    let currentFiles: FileInfo[] = [];
    files.subscribe(f => currentFiles = f)();
    
    if (currentFiles.length < 2) {
      console.log('Please select at least 2 PDF files');
      return;
    }
    
    isProcessing = true;
    progress = 0;
    
    try {
      // TODO: Call Rust backend to merge PDFs
      for (let i = 0; i <= 100; i += 10) {
        progress = i;
        await new Promise(r => setTimeout(r, 100));
      }
      
      console.log('Merge successful!');
      files.set([]);
    } catch (err) {
      console.error('Merge failed:', err);
    } finally {
      isProcessing = false;
      progress = 0;
    }
  }
</script>

<div class="p-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-800">PDF Merge</h1>
    <p class="text-gray-600 mt-2">Merge multiple PDF files into one</p>
  </div>
  
  <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold text-gray-700">Selected Files</h2>
      <button
        onclick={selectFiles}
        class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Add PDF Files
      </button>
    </div>
    
    {#if $files.length === 0}
      <div class="text-center py-12 text-gray-400">
        <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <p>Click the button above to add PDF files</p>
      </div>
    {:else}
      <ul class="space-y-2">
        {#each $files as file, index}
          <li class="flex items-center justify-between p-3 bg-gray-50 rounded-lg group">
            <div class="flex items-center gap-3 flex-1">
              <span class="text-gray-400 font-mono text-sm w-8">{index + 1}</span>
              <svg class="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A1 1 0 0112.293.707L13.293 2H12a1 1 0 01-1 1v1h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v3a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" clip-rule="evenodd" />
              </svg>
              <span class="flex-1 truncate text-gray-700">{file.name}</span>
            </div>
            <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
              {#if index > 0}
                <button 
                  onclick={() => moveUp(index)}
                  class="p-1 text-gray-400 hover:text-blue-600"
                  title="Move Up"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
                  </svg>
                </button>
              {/if}
              {#if index < $files.length - 1}
                <button 
                  onclick={() => moveDown(index)}
                  class="p-1 text-gray-400 hover:text-blue-600"
                  title="Move Down"
                >
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
              {/if}
              <button 
                onclick={() => removeFile(index)}
                class="p-1 text-gray-400 hover:text-red-600"
                title="Remove"
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
  
  {#if isProcessing}
    <div class="mb-6">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm text-gray-600">Merging...</span>
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
      Start Merge
    </button>
    <span class="text-sm text-gray-500">
      {$files.length} files selected
    </span>
  </div>
</div>
