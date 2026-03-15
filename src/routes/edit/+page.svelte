<script lang="ts">
  import { open, save } from '@tauri-apps/plugin-dialog';
  import { invoke } from '@tauri-apps/api/core';
  import { tick } from 'svelte';
  import type { TextBlock, TextMatch, TextBlocksResponse, TextSearchResponse, EditOperation, FontSettings } from '$lib/types';

  // File state
  let inputFile: { path: string; name: string } | null = $state(null);
  let totalPages = $state(0);
  let isLoadingPageCount = $state(false);

  // Mode state
  let editMode: 'search' | 'blocks' = $state('search');

  // Processing state
  let isProcessing = $state(false);
  let statusMessage = $state('');
  let isLoading = $state(false);

  // Search mode state
  let searchText = $state('');
  let replaceText = $state('');
  let caseSensitive = $state(false);
  let searchResults: TextMatch[] = $state([]);
  let selectedMatches: Set<number> = $state(new Set());

  // Block mode state
  let currentPage = $state(1);
  let pageImage = $state('');
  let pageWidth = $state(0);
  let pageHeight = $state(0);
  let imageWidth = $state(0);  // Actual rendered image width
  let imageHeight = $state(0); // Actual rendered image height
  let previewZoom = $state(1.5); // Zoom level for preview
  let textBlocks: TextBlock[] = $state([]);
  let selectedBlock: TextBlock | null = $state(null);
  let blockEditText = $state('');
  let previewContainerRef: HTMLDivElement | null = $state(null);  // Reference to preview container
  let renderedImageWidth = $state(0);  // Actual rendered width in DOM

  // Derived scale factor for positioning text blocks
  let effectiveScale = $derived(() => {
    const effectiveWidth = renderedImageWidth || imageWidth;
    return pageWidth > 0 ? effectiveWidth / pageWidth : previewZoom;
  });

  // Pending operations
  let pendingOperations: EditOperation[] = $state([]);

  // Effect to update rendered dimensions when image loads or window resizes
  $effect(() => {
    if (pageImage && imageWidth > 0) {
      // Wait for DOM update
      requestAnimationFrame(() => {
        updateRenderedDimensions();
      });
    }
  });

  // Handle window resize
  function handleResize() {
    updateRenderedDimensions();
  }

  // Font settings
  let fontSettings: FontSettings = $state({
    family: 'helv',
    size: 11,
    color: '#000000'
  });

  // File selection
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

        // Reset state
        searchResults = [];
        selectedMatches = new Set();
        textBlocks = [];
        selectedBlock = null;
        blockEditText = '';
        currentPage = 1;
        pendingOperations = [];
        pageImage = '';

        // Get page count
        await loadPageCount(selected);

        // Load initial data based on mode
        if (editMode === 'blocks') {
          await loadPagePreview(selected, 1);
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
      const response = await invoke<{ success: boolean; page_count?: number; error?: string }>('pdf_get_file_preview', {
        file: filePath,
        zoom: 0.1
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

  // Mode change
  async function onModeChange(mode: 'search' | 'blocks') {
    editMode = mode;

    if (mode === 'blocks' && inputFile) {
      await loadPagePreview(inputFile.path, currentPage);
    }
  }

  // Search mode functions
  async function performSearch() {
    if (!inputFile || !searchText.trim()) {
      statusMessage = '请输入搜索内容';
      return;
    }

    isLoading = true;
    statusMessage = '';

    try {
      const response = await invoke<TextSearchResponse>('pdf_search_text', {
        file: inputFile.path,
        search: searchText,
        caseSensitive,
        pages: null
      });

      if (response.success) {
        searchResults = response.matches || [];
        selectedMatches = new Set();
        if (searchResults.length === 0) {
          statusMessage = '未找到匹配内容';
        } else {
          statusMessage = `找到 ${response.total_matches || searchResults.length} 处匹配`;
        }
      } else {
        statusMessage = `搜索失败: ${response.error || '未知错误'}`;
        searchResults = [];
      }
    } catch (err) {
      console.error('Search failed:', err);
      statusMessage = `搜索失败: ${err}`;
      searchResults = [];
    } finally {
      isLoading = false;
    }
  }

  function toggleMatchSelection(index: number) {
    const newSelection = new Set(selectedMatches);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    selectedMatches = newSelection;
  }

  function selectAllMatches() {
    selectedMatches = new Set(searchResults.map((_, i) => i));
  }

  function clearMatchSelection() {
    selectedMatches = new Set();
  }

  function addReplaceOperation(matchIndex: number) {
    const match = searchResults[matchIndex];
    if (!match) return;

    const operation: EditOperation = {
      type: 'replace',
      page: match.page,
      search: match.text,
      replace: replaceText
      // No font settings - backend will auto-detect from original text
    };

    pendingOperations = [...pendingOperations, operation];
    statusMessage = `已添加替换操作 (页面 ${match.page})`;
  }

  function addBatchReplaceOperation() {
    if (selectedMatches.size === 0) {
      statusMessage = '请先选择要替换的匹配项';
      return;
    }

    const operations: EditOperation[] = [];
    selectedMatches.forEach(index => {
      const match = searchResults[index];
      if (match) {
        operations.push({
          type: 'replace',
          page: match.page,
          search: match.text,
          replace: replaceText
          // No font settings - backend will auto-detect from original text
        });
      }
    });

    pendingOperations = [...pendingOperations, ...operations];
    statusMessage = `已添加 ${operations.length} 个替换操作`;
    selectedMatches = new Set();
  }

  function addDeleteOperation(matchIndex: number) {
    const match = searchResults[matchIndex];
    if (!match) return;

    const operation: EditOperation = {
      type: 'delete',
      page: match.page,
      search: match.text
    };

    pendingOperations = [...pendingOperations, operation];
    statusMessage = `已添加删除操作 (页面 ${match.page})`;
  }

  function addBatchDeleteOperation() {
    if (selectedMatches.size === 0) {
      statusMessage = '请先选择要删除的匹配项';
      return;
    }

    const operations: EditOperation[] = [];
    selectedMatches.forEach(index => {
      const match = searchResults[index];
      if (match) {
        operations.push({
          type: 'delete',
          page: match.page,
          search: match.text
        });
      }
    });

    pendingOperations = [...pendingOperations, ...operations];
    statusMessage = `已添加 ${operations.length} 个删除操作`;
    selectedMatches = new Set();
  }

  // Block mode functions
  async function loadPagePreview(filePath: string, page: number) {
    if (page < 1 || (totalPages > 0 && page > totalPages)) return;

    isLoading = true;

    try {
      // Get page image with the new page-specific preview function
      const previewResponse = await invoke<{ success: boolean; image?: string; width?: number; height?: number; page_width?: number; page_height?: number; error?: string }>('pdf_get_page_preview', {
        file: filePath,
        page: page,
        zoom: previewZoom
      });

      if (previewResponse.success && previewResponse.image) {
        pageImage = previewResponse.image;
        imageWidth = previewResponse.width || 0;
        imageHeight = previewResponse.height || 0;
        pageWidth = previewResponse.page_width || 0;
        pageHeight = previewResponse.page_height || 0;

        // Debug: Log dimensions for troubleshooting
        console.log('Preview loaded:', {
          imageWidth,
          imageHeight,
          pageWidth,
          pageHeight,
          scale: pageWidth > 0 ? imageWidth / pageWidth : 'N/A'
        });
      } else {
        statusMessage = `加载页面预览失败: ${previewResponse.error || '未知错误'}`;
      }

      // Get text blocks
      const blocksResponse = await invoke<TextBlocksResponse>('pdf_get_text_blocks', {
        file: filePath,
        page
      });

      if (blocksResponse.success) {
        textBlocks = blocksResponse.blocks || [];
        // Update page dimensions from blocks response if not set
        if (!pageWidth && blocksResponse.page_width) {
          pageWidth = blocksResponse.page_width;
        }
        if (!pageHeight && blocksResponse.page_height) {
          pageHeight = blocksResponse.page_height;
        }

        // Debug: Log first block info
        if (textBlocks.length > 0) {
          console.log('Text blocks loaded:', textBlocks.length);
          console.log('First block:', {
            bbox: textBlocks[0].bbox,
            text: textBlocks[0].text?.substring(0, 30),
            font: textBlocks[0].font
          });
        } else {
          console.log('No text blocks found!');
        }
      } else {
        textBlocks = [];
        statusMessage = `获取文本块失败: ${blocksResponse.error || '未知错误'}`;
      }

      // Wait for DOM to update, then get actual rendered dimensions
      await tick();
      // Use a small timeout to ensure the image is fully rendered
      setTimeout(() => {
        updateRenderedDimensions();
      }, 50);
    } catch (err) {
      console.error('Failed to load page preview:', err);
      statusMessage = `加载预览失败: ${err}`;
    } finally {
      isLoading = false;
    }
  }

  async function goToPage(page: number) {
    if (!inputFile || page < 1 || page > totalPages) return;

    currentPage = page;
    selectedBlock = null;
    blockEditText = '';
    await loadPagePreview(inputFile.path, page);
  }

  function prevPage() {
    if (currentPage > 1) {
      goToPage(currentPage - 1);
    }
  }

  function nextPage() {
    if (currentPage < totalPages) {
      goToPage(currentPage + 1);
    }
  }

  function selectBlock(block: TextBlock) {
    selectedBlock = block;
    blockEditText = block.text;
    // Update font settings to match the detected font from the block
    if (block.font) {
      fontSettings = {
        family: block.font.family,
        size: block.font.size,
        color: block.font.color
      };
    }
  }

  function cancelBlockEdit() {
    selectedBlock = null;
    blockEditText = '';
  }

  function applyBlockEdit() {
    if (!selectedBlock || !inputFile) return;

    // Use detected font from block if available, otherwise use user settings
    const blockFont = selectedBlock.font || fontSettings;

    const operation: EditOperation = {
      type: 'replace',
      page: selectedBlock.page,
      search: selectedBlock.text,
      replace: blockEditText,
      bbox: selectedBlock.bbox,  // Pass bbox for accurate positioning
      font: blockFont
    };

    pendingOperations = [...pendingOperations, operation];
    statusMessage = `已添加修改操作 (页面 ${selectedBlock.page})`;

    // Update local block for visual feedback
    const blockToUpdate = selectedBlock;
    textBlocks = textBlocks.map(b =>
      b.id === blockToUpdate.id ? { ...b, text: blockEditText } : b
    );

    selectedBlock = null;
    blockEditText = '';
  }

  function deleteSelectedBlock() {
    if (!selectedBlock || !inputFile) return;

    const operation: EditOperation = {
      type: 'delete',
      page: selectedBlock.page,
      search: selectedBlock.text,
      bbox: selectedBlock.bbox  // Pass bbox for accurate positioning
    };

    pendingOperations = [...pendingOperations, operation];
    statusMessage = `已添加删除操作 (页面 ${selectedBlock.page})`;

    // Remove from local blocks for visual feedback
    const blockToDelete = selectedBlock;
    textBlocks = textBlocks.filter(b => b.id !== blockToDelete.id);

    selectedBlock = null;
    blockEditText = '';
  }

  // Update rendered image dimensions after DOM update
  function updateRenderedDimensions() {
    if (previewContainerRef) {
      const img = previewContainerRef.querySelector('img');
      if (img) {
        const newWidth = img.clientWidth;
        if (newWidth !== renderedImageWidth) {
          renderedImageWidth = newWidth;
          console.log('Rendered image width updated:', renderedImageWidth, 'Natural width:', imageWidth);
        }
      }
    }
  }

  // Convert PDF bbox to CSS positioning
  // Uses the derived effectiveScale for responsive positioning
  function getBlockStyle(bbox: [number, number, number, number] | { 0: number; 1: number; 2: number; 3: number }): string {
    // Handle both array and object formats
    const x0 = bbox[0];
    const y0 = bbox[1];
    const x1 = bbox[2];
    const y1 = bbox[3];

    const scale = effectiveScale();

    const left = x0 * scale;
    const top = y0 * scale;
    const width = (x1 - x0) * scale;
    const height = (y1 - y0) * scale;

    return `left: ${left}px; top: ${top}px; width: ${width}px; height: ${height}px;`;
  }

  // Operations management
  function removeOperation(index: number) {
    pendingOperations = pendingOperations.filter((_, i) => i !== index);
  }

  function clearAllOperations() {
    pendingOperations = [];
    statusMessage = '已清除所有待执行操作';
  }

  // Save changes
  async function saveChanges() {
    if (!inputFile || pendingOperations.length === 0) {
      statusMessage = '没有待执行的操作';
      return;
    }

    // Select output file using save dialog
    let outputPath: string | null = null;
    try {
      const selected = await save({
        filters: [{ name: 'PDF', extensions: ['pdf'] }],
        defaultPath: inputFile.path.replace(/\.pdf$/i, '_edited.pdf')
      });

      if (!selected) {
        return;
      }
      outputPath = selected;
    } catch (err) {
      console.error('Failed to select output:', err);
      statusMessage = `选择输出文件失败: ${err}`;
      return;
    }

    isProcessing = true;
    statusMessage = '正在处理...';

    try {
      const response = await invoke<{ success: boolean; operations_completed?: number; error?: string }>('pdf_edit_text', {
        file: inputFile.path,
        output: outputPath,
        operations: pendingOperations
      });

      if (response.success) {
        statusMessage = `保存成功！执行了 ${response.operations_completed || pendingOperations.length} 个操作`;
        pendingOperations = [];
      } else {
        statusMessage = `保存失败: ${response.error || '未知错误'}`;
      }
    } catch (err) {
      console.error('Failed to save changes:', err);
      statusMessage = `保存失败: ${err}`;
    } finally {
      isProcessing = false;
    }
  }
</script>

<svelte:head>
  <title>文字编辑 - PDF Editor</title>
</svelte:head>

<svelte:window on:resize={handleResize} />

<div class="p-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-800">文字编辑</h1>
    <p class="text-gray-600 mt-2">编辑PDF文件中的文字内容</p>
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

  {#if inputFile}
    <!-- Step 2: Mode Toggle -->
    <div class="bg-white rounded-lg shadow-sm p-4 mb-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">2. 选择编辑模式</h2>
      <div class="flex gap-2">
        <button
          onclick={() => onModeChange('search')}
          class="flex-1 py-2 px-4 rounded-lg font-medium transition-colors {editMode === 'search' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}"
        >
          搜索替换
        </button>
        <button
          onclick={() => onModeChange('blocks')}
          class="flex-1 py-2 px-4 rounded-lg font-medium transition-colors {editMode === 'blocks' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}"
        >
          文本块选择
        </button>
      </div>
    </div>

    <!-- Step 3: Edit Panel -->
    {#if editMode === 'search'}
      <!-- Search & Replace Mode -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 class="text-lg font-semibold text-gray-700 mb-4">3. 搜索和替换</h2>

        <!-- Notice -->
        <div class="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p class="text-sm text-amber-700">
            <strong>提示：</strong>替换操作会自动使用原文的字体、大小和颜色。由于字体兼容性问题，替换后的文本可能与原内容存在细微差异。
          </p>
          <p class="text-sm text-amber-700 mt-2">
            <strong>注意：</strong>由于 PDF 格式不易于编辑，替换文本的字数应尽量与原文相近。字数差异过大可能导致文字叠加或留白过多。
          </p>
        </div>

        <!-- Search Form -->
        <div class="space-y-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">搜索内容</label>
            <input
              type="text"
              bind:value={searchText}
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="输入要搜索的文字"
              onkeydown={(e) => e.key === 'Enter' && performSearch()}
            />
          </div>

          <div class="flex items-center gap-4">
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" bind:checked={caseSensitive} class="w-4 h-4" />
              <span class="text-sm text-gray-600">区分大小写</span>
            </label>
            <button
              onclick={performSearch}
              disabled={isLoading || !searchText.trim()}
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {#if isLoading}
                搜索中...
              {:else}
                搜索
              {/if}
            </button>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">替换为</label>
            <input
              type="text"
              bind:value={replaceText}
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="输入替换后的文字（留空则删除）"
            />
          </div>
        </div>

        <!-- Search Results -->
        {#if searchResults.length > 0}
          <div class="border-t pt-4">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-sm font-medium text-gray-600">搜索结果 ({searchResults.length})</h3>
              <div class="flex gap-2">
                <button
                  onclick={selectAllMatches}
                  class="text-xs text-blue-600 hover:text-blue-700"
                >
                  全选
                </button>
                <button
                  onclick={clearMatchSelection}
                  class="text-xs text-gray-500 hover:text-gray-700"
                >
                  清除选择
                </button>
              </div>
            </div>

            <!-- Batch Operations -->
            {#if selectedMatches.size > 0}
              <div class="mb-3 p-3 bg-blue-50 rounded-lg flex items-center justify-between">
                <span class="text-sm text-blue-700">已选择 {selectedMatches.size} 项</span>
                <div class="flex gap-2">
                  <button
                    onclick={addBatchReplaceOperation}
                    class="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    批量替换
                  </button>
                  <button
                    onclick={addBatchDeleteOperation}
                    class="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
                  >
                    批量删除
                  </button>
                </div>
              </div>
            {/if}

            <div class="max-h-60 overflow-y-auto space-y-2">
              {#each searchResults as match, index}
                <div
                  class="p-3 border rounded-lg cursor-pointer transition-colors {selectedMatches.has(index) ? 'bg-blue-50 border-blue-300' : 'hover:bg-gray-50'}"
                  onclick={() => toggleMatchSelection(index)}
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="text-xs font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                          第 {match.page} 页
                        </span>
                        {#if selectedMatches.has(index)}
                          <svg class="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                          </svg>
                        {/if}
                      </div>
                      <p class="text-sm text-gray-700 truncate">{match.context}</p>
                    </div>
                    <div class="flex gap-1 shrink-0">
                      <button
                        onclick={(e) => { e.stopPropagation(); addReplaceOperation(index); }}
                        class="p-1.5 text-green-600 hover:bg-green-50 rounded"
                        title="替换此项"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </button>
                      <button
                        onclick={(e) => { e.stopPropagation(); addDeleteOperation(index); }}
                        class="p-1.5 text-red-600 hover:bg-red-50 rounded"
                        title="删除此项"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/if}
      </div>
    {:else}
      <!-- Block Selection Mode -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 class="text-lg font-semibold text-gray-700 mb-4">3. 选择文本块</h2>

        <!-- Page Navigation -->
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center gap-2">
            <button
              onclick={prevPage}
              disabled={currentPage <= 1}
              class="p-2 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <span class="text-sm text-gray-600">
              第 <input
                type="number"
                bind:value={currentPage}
                min="1"
                max={totalPages}
                class="w-12 px-2 py-1 border rounded text-center"
                onchange={() => goToPage(currentPage)}
              /> 页 / 共 {totalPages} 页
            </span>
            <button
              onclick={nextPage}
              disabled={currentPage >= totalPages}
              class="p-2 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
          <button
            onclick={() => inputFile && loadPagePreview(inputFile.path, currentPage)}
            disabled={isLoading}
            class="text-sm text-blue-600 hover:text-blue-700"
          >
            刷新
          </button>
        </div>

        <!-- PDF Preview with Text Blocks -->
        <div
          bind:this={previewContainerRef}
          class="relative border rounded-lg overflow-auto bg-gray-100"
          style="max-height: 600px;"
        >
          {#if isLoading}
            <div class="flex items-center justify-center h-96">
              <svg class="w-8 h-8 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              <span class="ml-2 text-gray-600">加载中...</span>
            </div>
          {:else if pageImage}
            <div class="flex justify-center">
              <div class="relative inline-block flex-shrink-0" style="min-width: {imageWidth}px;">
                <img
                  src="data:image/png;base64,{pageImage}"
                  alt="Page {currentPage}"
                  class="block"
                  style="width: {imageWidth}px; height: {imageHeight}px;"
                  onload={() => updateRenderedDimensions()}
                />

                <!-- Text Block Overlays -->
                {#each textBlocks as block}
                  <button
                    onclick={() => selectBlock(block)}
                    class="absolute transition-all {selectedBlock?.id === block.id ? 'ring-2 ring-blue-500 bg-blue-100/50' : 'bg-yellow-200/30 hover:bg-yellow-300/50'}"
                    style={getBlockStyle(block.bbox)}
                    title={block.text}
                  >
                    <span class="sr-only">{block.text}</span>
                  </button>
                {/each}
              </div>
            </div>
          {:else}
            <div class="flex items-center justify-center h-96 text-gray-500">
              请加载页面预览
            </div>
          {/if}
        </div>

        <!-- Selected Block Edit Form -->
        {#if selectedBlock}
          <div class="mt-4 p-4 bg-gray-50 rounded-lg">
            <h3 class="text-sm font-medium text-gray-700 mb-2">编辑文本块</h3>
            {#if selectedBlock.font}
              <div class="text-xs text-gray-500 mb-2 flex items-center gap-3">
                <span>原字体: {selectedBlock.font.family}</span>
                <span>字号: {selectedBlock.font.size}</span>
                <span class="flex items-center gap-1">
                  颜色:
                  <span class="w-4 h-4 rounded border" style="background-color: {selectedBlock.font.color}"></span>
                </span>
              </div>
            {/if}
            <textarea
              bind:value={blockEditText}
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 mb-3"
              rows="3"
              placeholder="输入新文本"
            ></textarea>
            <div class="flex gap-2">
              <button
                onclick={applyBlockEdit}
                class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
              >
                应用修改
              </button>
              <button
                onclick={deleteSelectedBlock}
                class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
              >
                删除
              </button>
              <button
                onclick={cancelBlockEdit}
                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                取消
              </button>
            </div>
          </div>
        {:else if textBlocks.length > 0}
          <p class="mt-3 text-sm text-gray-500 text-center">
            点击高亮区域选择文本块进行编辑
          </p>
        {:else}
          <p class="mt-3 text-sm text-gray-500 text-center">
            当前页面没有检测到文本块
          </p>
        {/if}
      </div>
    {/if}

    <!-- Font Settings - Only shown in block mode -->
    {#if editMode === 'blocks'}
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 class="text-lg font-semibold text-gray-700 mb-4">4. 字体设置</h2>
        <p class="text-xs text-gray-500 mb-3">
          提示：选择文本块时会自动检测并应用原字体，您可以在编辑时调整。
        </p>
        <div class="grid grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">字体</label>
            <select
              bind:value={fontSettings.family}
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <optgroup label="中文字体">
                <option value="FangSong">仿宋 (FangSong)</option>
                <option value="SimSun">宋体 (SimSun)</option>
                <option value="SimHei">黑体 (SimHei)</option>
                <option value="KaiTi">楷体 (KaiTi)</option>
                <option value="DengXian">等线 (DengXian)</option>
                <option value="Microsoft YaHei">微软雅黑</option>
              </optgroup>
              <optgroup label="西文字体">
                <option value="Helvetica">Helvetica</option>
                <option value="Times New Roman">Times New Roman</option>
                <option value="Courier New">Courier New</option>
                <option value="Arial">Arial</option>
              </optgroup>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">字号</label>
            <input
              type="number"
              bind:value={fontSettings.size}
              min="6"
              max="72"
              class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-1">颜色</label>
            <div class="flex items-center gap-2">
              <input
                type="color"
                bind:value={fontSettings.color}
                class="w-10 h-10 border rounded cursor-pointer"
              />
              <input
                type="text"
                bind:value={fontSettings.color}
                class="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Pending Operations -->
    {#if pendingOperations.length > 0}
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-700">待执行操作 ({pendingOperations.length})</h2>
          <button
            onclick={clearAllOperations}
            class="text-sm text-red-600 hover:text-red-700"
          >
            清除全部
          </button>
        </div>
        <div class="max-h-40 overflow-y-auto space-y-2">
          {#each pendingOperations as op, index}
            <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
              <div class="flex items-center gap-2">
                <span class="text-xs font-medium {op.type === 'replace' ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'} px-2 py-0.5 rounded">
                  {op.type === 'replace' ? '替换' : '删除'}
                </span>
                <span class="text-xs text-gray-500">第 {op.page} 页</span>
                <span class="text-sm text-gray-700 truncate max-w-xs">
                  {#if op.search}
                    "{op.search}" {#if op.replace}→ "{op.replace}"{/if}
                  {/if}
                </span>
              </div>
              <button
                onclick={() => removeOperation(index)}
                class="text-gray-400 hover:text-red-500"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Status Message -->
    {#if statusMessage}
      <div class="mb-6 p-4 rounded-lg {isProcessing ? 'bg-blue-50 text-blue-700' : statusMessage.includes('成功') ? 'bg-green-50 text-green-700' : statusMessage.includes('已添加') ? 'bg-yellow-50 text-yellow-700' : 'bg-red-50 text-red-700'}">
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

    <!-- Save Button -->
    <button
      onclick={saveChanges}
      disabled={pendingOperations.length === 0 || isProcessing}
      class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
    >
      {#if isProcessing}
        保存中...
      {:else}
        保存更改 ({pendingOperations.length} 个操作)
      {/if}
    </button>
  {/if}
</div>
