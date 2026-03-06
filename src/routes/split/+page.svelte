<script lang="ts">
  import { open } from '@tauri-apps/plugin-dialog';
  import { save } from '@tauri-apps/plugin-dialog';
  import type { FileEntry } from '$lib/types';
  
  let inputFile: FileEntry | null = null;
  let outputDir: string = $state('');
  let splitMode: 'range' | 'fixed' | 'extract' = $state('range');
  let isProcessing = $state(false);
  
  // Range mode
  let ranges: [number, number][] = $state([]);
  
  // Fixed mode
  let pagesPerFile = $state(5);
  
  // Extract mode
  let pagesToExtract = $state('');
  
  async function selectFile() {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'PDF',
          extensions: ['pdf']
        }]
      });
      
      if (selected) {
        inputFile = {
          path: selected,
          name: selected.split(/[/\\]/).pop() || selected,
          pageCount: 0
        };
      }
    } catch (err) {
    console.error('Failed to select file:', err);
    }
  }
  
  async function selectOutputDir() {
    try {
      const selected = await open({
        directory: true,
        multiple: false
      });
      
      if (selected) {
        outputDir = selected;
      }
    } catch (err) {
      console.error('Failed to select directory:', err);
    }
  }
  
  async function splitFile() {
    if (!inputFile || !outputDir) {
      console.log('请选择输入文件和输出目录');
      return;
    }
    
    isProcessing = true;
    
    try {
      // TODO: Call Rust backend to split PDF
      console.log('分拆成功！（功能待实现）');
      inputFile = null;
    } catch (err) {
      console.error('分拆失败:', err);
    } finally {
      isProcessing = false;
    }
  }
  
  function addRange() {
    ranges = [...ranges, [1, 1]];
  }
  
  function removeRange(index: number) {
    ranges = ranges.filter((_, i) => i !== index);
  }
</script>

<div class="p-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-800">PDF分拆</h1>
    <p class="text-gray-600 mt-2">将PDF文件分拆为多个文件</p>
  </div>
  
  <div class="grid grid-cols-2 gap-6">
    <!-- Input File -->
    <div class="bg-white rounded-lg shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">选择PDF文件</h2>
      <button
        onclick={selectFile}
        class="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
      >
        {#if inputFile}
          <div class="flex items-center gap-2">
            <svg class="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A1 1 0 0112.293.707L15.293 5H12a1 1 0 00-1 1v1h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v3a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" clip-rule="evenodd" />
            </svg>
            <span class="text-gray-700">{inputFile.name}</span>
          </div>
        {:else}
          <div class="text-center py-4">
            <svg class="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="text-gray-500">点击选择PDF文件</p>
          </div>
        {/if}
      </button>
    </div>
    
    <!-- Output Directory -->
    <div class="bg-white rounded-lg shadow-sm p-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">输出目录</h2>
      <button
        onclick={selectOutputDir}
        class="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
      >
        {#if outputDir}
          <span class="text-gray-700">{outputDir}</span>
        {:else}
          <div class="text-center py-4">
            <svg class="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <p class="text-gray-500">点击选择输出目录</p>
          </div>
        {/if}
      </button>
    </div>
  </div>
  
  <!-- Split Mode -->
  <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
    <h2 class="text-lg font-semibold text-gray-700 mb-4">分拆模式</h2>
    <div class="space-y-3">
      <label class="flex items-center gap-3 cursor-pointer">
        <input type="radio" bind:group={splitMode} value="range" name="splitMode" class="w-4 h-4" />
        <span class="text-gray-700">按页码范围分拆</span>
      </label>
      <label class="flex items-center gap-3 cursor-pointer">
        <input type="radio" bind:group={splitMode} value="fixed" name="splitMode" class="w-4 h-4" />
        <span class="text-gray-700">按固定页数分拆</span>
      </label>
      <label class="flex items-center gap-3 cursor-pointer">
        <input type="radio" bind:group={splitMode} value="extract" name="splitMode" class="w-4 h-4" />
        <span class="text-gray-700">提取特定页面</span>
      </label>
    </div>
    
    <!-- Range Mode Options -->
    {#if splitMode === 'range'}
      <div class="mt-4 space-y-2">
        {#each ranges as range, index}
          <div class="flex items-center gap-2">
            <input type="number" bind:value={range[0]} class="w-20 px-2 py-1 border rounded" placeholder="开始页" />
            <span class="text-gray-500">-</span>
            <input type="number" bind:value={range[1]} class="w-20 px-2 py-1 border rounded" placeholder="结束页" />
            <button onclick={() => removeRange(index)} class="text-red-500 hover:text-red-700">删除</button>
          </div>
        {/each}
        <button onclick={addRange} class="text-blue-600 hover:text-blue-700 text-sm">+ 添加范围</button>
      </div>
    {:else if splitMode === 'fixed'}
      <div class="mt-4">
        <label class="text-sm text-gray-600">每个文件页数：</label>
        <input type="number" bind:value={pagesPerFile} class="w-24 px-3 py-1 border rounded mt-1" />
      </div>
    {:else if splitMode === 'extract'}
      <div class="mt-4">
        <label class="text-sm text-gray-600">要提取的页码（用逗号分隔）：</label>
        <input type="text" bind:value={pagesToExtract} class="w-full px-3 py-1 border rounded mt-1" placeholder="例如: 1,3,5,7" />
      </div>
    {/if}
  </div>
  
  <!-- Split Button -->
  <button
    onclick={splitFile}
    disabled={!inputFile || !outputDir || isProcessing}
    class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
  >
    开始分拆
  </button>
</div>
