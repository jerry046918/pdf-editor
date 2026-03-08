<script lang="ts">
  import { open } from '@tauri-apps/plugin-dialog';
  import { invoke } from '@tauri-apps/api/core';

  interface Thumbnail {
    page: number;
    image: string;
    width: number;
    height: number;
  }

  interface ThumbnailsResponse {
    success: boolean;
    error?: string;
    thumbnails?: Thumbnail[];
    page_count?: number;
  }

  interface PdfResponse {
    success: boolean;
    error?: string;
    files?: string[];
    total_files?: number;
  }

  interface FilePreviewResponse {
    success: boolean;
    error?: string;
    page_count?: number;
  }

  let inputFile: { path: string; name: string } | null = $state(null);
  let splitMode: 'range' | 'fixed' | 'extract' = $state('range');
  let isProcessing = $state(false);
  let statusMessage = $state('');
  let isLoadingThumbnails = $state(false);
  let isLoadingPageCount = $state(false);
  let thumbnails: Thumbnail[] = $state([]);
  let selectedPages: Set<number> = $state(new Set());
  let thumbnailsLoaded = $state(false);
  let totalPages = $state(0);
  let rangeErrors: Map<number, string> = $state(new Map());
  
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
        filters: [{ name: 'PDF', extensions: ['pdf'] }]
      });
      
      if (selected && typeof selected === 'string') {
        inputFile = {
          path: selected,
          name: selected.split(/[/\\]/).pop() || selected
        };
        // Reset state when file changes
        thumbnails = [];
        thumbnailsLoaded = false;
        selectedPages = new Set();
        pagesToExtract = '';
        ranges = [];
        rangeErrors = new Map();
        
        // Get total page count
        await loadPageCount(selected);
        
        // Load thumbnails if already in extract mode
        if (splitMode === 'extract') {
          loadThumbnails(selected);
        }
      }
    } catch (err) {
      console.error('Failed to select file:', err);
      statusMessage = `选择文件失败: ${err}`;
    }
  }

  async function loadPageCount(filePath: string) {
    isLoadingPageCount = true;
    try {
      const response = await invoke<FilePreviewResponse>('pdf_get_file_preview', {
        file: filePath,
        zoom: 0.1 // 最小缩放以加快速度
      });
      
      if (response.success && response.page_count) {
        totalPages = response.page_count;
      } else {
        totalPages = 0;
        statusMessage = `获取页数失败: ${response.error || '未知错误'}`;
      }
    } catch (err) {
      console.error('Failed to get page count:', err);
      totalPages = 0;
    } finally {
      isLoadingPageCount = false;
    }
  }

  async function loadThumbnails(filePath: string) {
    if (thumbnailsLoaded) return; // Prevent duplicate loading
    
    isLoadingThumbnails = true;
    thumbnails = [];
    
    try {
      const response = await invoke<ThumbnailsResponse>('pdf_get_thumbnails', {
        file: filePath,
        max_pages: 50,
        zoom: 0.3
      });
      
      if (response.success && response.thumbnails) {
        thumbnails = response.thumbnails;
        thumbnailsLoaded = true;
      } else {
        statusMessage = `加载预览失败: ${response.error || '未知错误'}`;
      }
    } catch (err) {
      console.error('Failed to load thumbnails:', err);
      statusMessage = `加载预览失败: ${err}`;
    } finally {
      isLoadingThumbnails = false;
    }
  }

  function onSplitModeChange(mode: 'range' | 'fixed' | 'extract') {
    splitMode = mode;
    // Load thumbnails when switching to extract mode if file is selected
    if (mode === 'extract' && inputFile && !thumbnailsLoaded) {
      loadThumbnails(inputFile.path);
    }
  }

  function togglePage(page: number) {
    const newSelection = new Set(selectedPages);
    if (newSelection.has(page)) {
      newSelection.delete(page);
    } else {
      newSelection.add(page);
    }
    selectedPages = newSelection;
    pagesToExtract = Array.from(selectedPages).sort((a, b) => a - b).join(',');
  }

  function selectAllPages() {
    if (thumbnails.length > 0) {
      selectedPages = new Set(thumbnails.map(t => t.page));
      pagesToExtract = Array.from(selectedPages).sort((a, b) => a - b).join(',');
    }
  }

  function clearSelection() {
    selectedPages = new Set();
    pagesToExtract = '';
  }

  // 验证单个范围
  function validateRange(index: number): boolean {
    const range = ranges[index];
    if (!range) return true;
    
    const [start, end] = range;
    const errors = new Map(rangeErrors);
    
    // 清除该范围的错误
    errors.delete(index);
    
    // 检查结束页必须大于等于开始页
    if (end < start) {
      errors.set(index, '结束页必须大于等于开始页');
      rangeErrors = errors;
      return false;
    }
    
    // 检查最大页码不超过总页数
    if (totalPages > 0 && end > totalPages) {
      errors.set(index, `最大页码不能超过 ${totalPages}`);
      rangeErrors = errors;
      return false;
    }
    
    // 检查页码必须大于0
    if (start < 1 || end < 1) {
      errors.set(index, '页码必须大于0');
      rangeErrors = errors;
      return false;
    }
    
    // 检查范围之间是否交叉
    for (let i = 0; i < ranges.length; i++) {
      if (i === index) continue;
      const [otherStart, otherEnd] = ranges[i];
      
      // 检查是否交叉: [start, end] 与 [otherStart, otherEnd] 有交集
      if (start <= otherEnd && end >= otherStart) {
        errors.set(index, `与范围${i + 1}交叉`);
        rangeErrors = errors;
        return false;
      }
    }
    
    rangeErrors = errors;
    return true;
  }

  // 验证所有范围
  function validateAllRanges(): boolean {
    if (ranges.length === 0) {
      statusMessage = '请至少添加一个页码范围';
      return false;
    }
    
    let allValid = true;
    for (let i = 0; i < ranges.length; i++) {
      if (!validateRange(i)) {
        allValid = false;
      }
    }
    
    if (!allValid) {
      statusMessage = '请修正页码范围错误';
    }
    
    return allValid;
  }

  // 检查是否可以添加新范围
  function canAddRange(): boolean {
    if (totalPages === 0 || ranges.length === 0) return true;
    
    // 计算当前范围覆盖的最大页码
    let maxCoveredPage = 0;
    for (const [start, end] of ranges) {
      maxCoveredPage = Math.max(maxCoveredPage, end);
    }
    
    // 如果已覆盖到最大页码，检查是否有空白区域
    if (maxCoveredPage >= totalPages) {
      // 检查是否有空白区域
      const nextAvailable = findNextAvailableStart();
      return nextAvailable <= totalPages;
    }
    
    return true;
  }

  // 添加新范围
  function addRange() {
    // 检查是否可以添加新范围
    if (!canAddRange()) {
      statusMessage = '所有页面已被覆盖';
      return;
    }
    
    // 计算新范围的起始页
    let newStart = 1;
    
    if (ranges.length > 0) {
      // 从上一个范围的结束页+1开始
      const lastRange = ranges[ranges.length - 1];
      newStart = lastRange[1] + 1;
      
      // 如果超出总页数，则从第一个空白区域开始
      if (totalPages > 0 && newStart > totalPages) {
        // 找到第一个可用的空白区域
        newStart = findNextAvailableStart();
      }
    }
    
    // 计算新范围的结束页
    let newEnd = newStart;
    if (totalPages > 0 && newEnd > totalPages) {
      newEnd = totalPages;
    }
    
    ranges = [...ranges, [newStart, newEnd]];
    statusMessage = ''; // 清除提示
  }

  // 找到下一个可用的起始页
  function findNextAvailableStart(): number {
    if (ranges.length === 0) return 1;
    
    // 收集所有已使用的范围
    const usedRanges = ranges.map(r => [r[0], r[1]] as [number, number]).sort((a, b) => a[0] - b[0]);
    
    // 找到第一个空白区域
    let currentEnd = 0;
    for (const [start, end] of usedRanges) {
      if (start > currentEnd + 1) {
        // 找到空白区域
        return currentEnd + 1;
      }
      currentEnd = Math.max(currentEnd, end);
    }
    
    // 没有空白区域，返回最后一个范围之后
    return currentEnd + 1;
  }

  function removeRange(index: number) {
    ranges = ranges.filter((_, i) => i !== index);
    // 清除该范围的错误
    const errors = new Map(rangeErrors);
    errors.delete(index);
    rangeErrors = errors;
  }

  async function splitFile() {
    if (!inputFile) {
      statusMessage = '请选择输入文件';
      return;
    }
    
    // Validate range mode
    if (splitMode === 'range' && !validateAllRanges()) {
      return;
    }
    
    // Validate extract mode
    if (splitMode === 'extract' && selectedPages.size === 0) {
      statusMessage = '请选择要提取的页面';
      return;
    }
    
    // 弹出目录选择对话框
    let outputDir: string | null = null;
    try {
      const selected = await open({
        directory: true,
        multiple: false
      });
      
      if (!selected || typeof selected !== 'string') {
        return; // 用户取消
      }
      outputDir = selected;
    } catch (err) {
      console.error('Failed to select directory:', err);
      statusMessage = `选择目录失败: ${err}`;
      return;
    }
    
    isProcessing = true;
    statusMessage = '正在分拆PDF文件...';
    
    try {
      // Generate prefix from input filename: test.pdf -> test_split
      const baseName = inputFile.name.replace(/\.pdf$/i, '');
      const prefix = `${baseName}_split`;
      let options: Record<string, unknown> = {};
      
      if (splitMode === 'range') {
        options = { ranges, prefix };
      } else if (splitMode === 'fixed') {
        options = { pages_per_file: pagesPerFile, prefix };
      } else if (splitMode === 'extract') {
        const pages = Array.from(selectedPages).sort((a, b) => a - b);
        options = { pages, prefix };
      }
      
      const response = await invoke<PdfResponse>('pdf_split', {
        file: inputFile.path,
        outputDir: outputDir,
        mode: splitMode,
        options
      });
      
      if (response.success) {
        statusMessage = `分拆成功！生成了 ${response.total_files || response.files?.length || 0} 个文件`;
        // Reset state
        inputFile = null;
        thumbnails = [];
        thumbnailsLoaded = false;
        selectedPages = new Set();
        ranges = [];
        rangeErrors = new Map();
        totalPages = 0;
        pagesToExtract = '';
      } else {
        statusMessage = `分拆失败: ${response.error || '未知错误'}`;
      }
    } catch (err) {
      console.error('分拆失败:', err);
      statusMessage = `分拆失败: ${err}`;
    } finally {
      isProcessing = false;
    }
  }
</script>

<div class="p-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-800">PDF分拆</h1>
    <p class="text-gray-600 mt-2">将PDF文件分拆为多个文件</p>
  </div>
  
  <!-- Step 1: File Selection -->
  <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
    <h2 class="text-lg font-semibold text-gray-700 mb-4">1. 选择PDF文件</h2>
    <button
      onclick={selectFile}
      class="w-full px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
    >
      {#if inputFile}
        <div class="flex items-center justify-center gap-3">
          <svg class="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A1 1 0 0112.293.707L15.293 5H12a1 1 0 00-1 1v1h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v3a2 2 0 01-2 2H6a2 2 0 01-2-2V6z" clip-rule="evenodd" />
          </svg>
          <span class="text-gray-700 truncate">{inputFile.name}</span>
          {#if isLoadingPageCount}
            <span class="text-xs text-gray-400">获取页数中...</span>
          {:else if totalPages > 0}
            <span class="text-xs text-blue-600 font-medium bg-blue-50 px-2 py-0.5 rounded-full">共 {totalPages} 页</span>
          {/if}
        </div>
      {:else}
        <div class="text-center py-4">
          <svg class="w-12 h-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p class="text-gray-500 text-sm">点击选择PDF文件</p>
        </div>
      {/if}
    </button>
  </div>

  <!-- Step 2: Split Mode -->
  {#if inputFile}
    <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">2. 选择分拆模式</h2>
      <div class="space-y-3">
        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50 transition-colors {splitMode === 'range' ? 'bg-blue-50 ring-1 ring-blue-200' : ''}">
          <input type="radio" bind:group={splitMode} value="range" name="splitMode" class="w-4 h-4" onchange={() => onSplitModeChange('range')} />
          <div>
            <span class="text-gray-700 font-medium">按页码范围分拆</span>
            <p class="text-sm text-gray-500">指定页码范围，每个范围生成一个文件</p>
          </div>
        </label>
        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50 transition-colors {splitMode === 'fixed' ? 'bg-blue-50 ring-1 ring-blue-200' : ''}">
          <input type="radio" bind:group={splitMode} value="fixed" name="splitMode" class="w-4 h-4" onchange={() => onSplitModeChange('fixed')} />
          <div>
            <span class="text-gray-700 font-medium">按固定页数分拆</span>
            <p class="text-sm text-gray-500">每隔N页生成一个文件</p>
          </div>
        </label>
        <label class="flex items-center gap-3 cursor-pointer p-3 rounded-lg hover:bg-gray-50 transition-colors {splitMode === 'extract' ? 'bg-blue-50 ring-1 ring-blue-200' : ''}">
          <input type="radio" bind:group={splitMode} value="extract" name="splitMode" class="w-4 h-4" onchange={() => onSplitModeChange('extract')} />
          <div>
            <span class="text-gray-700 font-medium">提取选中页面</span>
            <p class="text-sm text-gray-500">通过预览选择需要的页面，生成单个文件</p>
          </div>
        </label>
      </div>
      
      <!-- Range Mode Options -->
      {#if splitMode === 'range'}
        <div class="mt-4 pt-4 border-t">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-medium text-gray-600">页码范围设置</h3>
            {#if totalPages > 0}
              <span class="text-xs text-gray-400">文档共 {totalPages} 页</span>
            {/if}
          </div>
          <div class="space-y-2">
            {#each ranges as range, index}
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs text-gray-400 w-12 shrink-0">范围 {index + 1}</span>
                <input 
                  type="number" 
                  bind:value={range[0]} 
                  min="1" 
                  max={totalPages || undefined}
                  class="w-20 px-2 py-1 border rounded text-sm {rangeErrors.get(index) ? 'border-red-500 bg-red-50' : ''}" 
                  placeholder="开始页"
                  onchange={() => validateRange(index)}
                />
                <span class="text-gray-400">-</span>
                <input 
                  type="number" 
                  bind:value={range[1]} 
                  min="1" 
                  max={totalPages || undefined}
                  class="w-20 px-2 py-1 border rounded text-sm {rangeErrors.get(index) ? 'border-red-500 bg-red-50' : ''}" 
                  placeholder="结束页"
                  onchange={() => validateRange(index)}
                />
                <span class="text-xs text-gray-400">页</span>
                {#if rangeErrors.get(index)}
                  <span class="text-xs text-red-500 flex-1">{rangeErrors.get(index)}</span>
                {:else}
                  <span class="text-xs text-gray-400 flex-1">({range[1] - range[0] + 1} 页)</span>
                {/if}
                <button 
                  onclick={() => removeRange(index)} 
                  class="text-red-500 hover:text-red-700 px-2 py-1 text-sm hover:bg-red-50 rounded"
                >
                  删除
                </button>
              </div>
            {/each}
            <div class="pt-2">
              {#if canAddRange()}
                <button 
                  onclick={addRange} 
                  class="text-blue-600 hover:text-blue-700 text-sm flex items-center gap-1"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                  添加范围
                </button>
              {:else}
                <p class="text-xs text-amber-600 flex items-center gap-1">
                  <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                  所有页面已被覆盖
                </p>
              {/if}
            </div>
            {#if ranges.length === 0}
              <p class="text-xs text-gray-400 mt-2">点击"添加范围"开始设置分拆范围</p>
            {/if}
          </div>
        </div>
      {:else if splitMode === 'fixed'}
        <div class="mt-4 pt-4 border-t">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-medium text-gray-600">固定页数设置</h3>
            {#if totalPages > 0}
              <span class="text-xs text-gray-400">文档共 {totalPages} 页</span>
            {/if}
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-600">每个文件包含：</span>
            <input 
              type="number" 
              bind:value={pagesPerFile} 
              min="1" 
              max={totalPages || undefined}
              class="w-24 px-3 py-1 border rounded text-sm" 
            />
            <span class="text-sm text-gray-600">页</span>
            {#if totalPages > 0 && pagesPerFile > 0}
              <span class="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                将生成 {Math.ceil(totalPages / pagesPerFile)} 个文件
              </span>
            {/if}
          </div>
        </div>
      {:else if splitMode === 'extract'}
        <div class="mt-4 pt-4 border-t">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-medium text-gray-600">提取页面设置</h3>
            {#if totalPages > 0}
              <span class="text-xs text-gray-400">文档共 {totalPages} 页</span>
            {/if}
          </div>
          {#if selectedPages.size > 0}
            <p class="text-sm text-green-600 mb-2 flex items-center gap-1">
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
              </svg>
              已选择 {selectedPages.size} 个页面
            </p>
          {:else}
            <p class="text-sm text-gray-500 mb-2">请在下方预览中点击选择要提取的页面</p>
          {/if}
          <input 
            type="text" 
            bind:value={pagesToExtract} 
            class="w-full px-3 py-2 border rounded text-sm" 
            placeholder="或直接输入页码，如: 1,3,5,7-10" 
          />
        </div>
      {/if}
    </div>
  {/if}

  <!-- Thumbnail Grid - Only show in extract mode -->
  {#if splitMode === 'extract' && inputFile}
    <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-700">3. 选择页面</h2>
        {#if thumbnails.length > 0}
          <div class="flex gap-2">
            <button
              onclick={selectAllPages}
              class="px-3 py-1 text-sm text-blue-600 hover:text-blue-700 border border-blue-300 rounded hover:bg-blue-50 transition-colors"
            >
              全选
            </button>
            <button
              onclick={clearSelection}
              class="px-3 py-1 text-sm text-gray-600 hover:text-gray-700 border border-gray-300 rounded hover:bg-gray-50 transition-colors"
            >
              清除选择
            </button>
          </div>
        {/if}
      </div>
      
      {#if isLoadingThumbnails}
        <div class="flex items-center justify-center py-8">
          <svg class="w-8 h-8 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          <span class="ml-2 text-gray-600">加载预览中...</span>
        </div>
      {:else if thumbnails.length > 0}
        <div class="grid grid-cols-5 gap-3 max-h-96 overflow-y-auto">
          {#each thumbnails as thumb}
            <button
              onclick={() => togglePage(thumb.page)}
              class="relative rounded overflow-hidden transition-all bg-white {selectedPages.has(thumb.page) ? 'ring-2 ring-blue-500' : 'ring-1 ring-gray-200 hover:ring-gray-300'}"
            >
              <img
                src="data:image/png;base64,{thumb.image}"
                alt="Page {thumb.page}"
                class="w-full h-auto bg-white"
              />
              <div class="absolute inset-0 bg-black/0 hover:bg-black/10 transition-all"></div>
              <div class="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs py-1 text-center">
                {thumb.page}
              </div>
              {#if selectedPages.has(thumb.page)}
                <div class="absolute top-1 right-1 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                  <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                  </svg>
                </div>
              {/if}
            </button>
          {/each}
        </div>
        {#if totalPages > thumbnails.length}
          <p class="text-xs text-gray-400 mt-3 text-center">
            显示前 {thumbnails.length} 页，共 {totalPages} 页
          </p>
        {/if}
      {:else}
        <div class="text-center py-8">
          <div class="text-gray-400 mb-2">
            <svg class="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <p class="text-gray-500 text-sm">加载页面预览中...</p>
        </div>
      {/if}
    </div>
  {/if}

  <!-- Status Message -->
  {#if statusMessage}
    <div class="mb-6 p-4 rounded-lg {isProcessing ? 'bg-blue-50 text-blue-700' : statusMessage.includes('成功') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}">
      <div class="flex items-center gap-2">
        {#if isProcessing}
          <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
        {/if}
        <span>{statusMessage}</span>
      </div>
    </div>
  {/if}

  <!-- Split Button -->
  <button
    onclick={splitFile}
    disabled={!inputFile || isProcessing || (splitMode === 'extract' && selectedPages.size === 0) || (splitMode === 'range' && (ranges.length === 0 || rangeErrors.size > 0))}
    class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
  >
    {#if isProcessing}
      处理中...
    {:else}
      开始分拆
    {/if}
  </button>
</div>
