<script lang="ts">
  import { open, save } from '@tauri-apps/plugin-dialog';
  import { invoke } from '@tauri-apps/api/core';
  import { readFile } from '@tauri-apps/plugin-fs';
  import { writable } from 'svelte/store';

  interface ImageInfo {
    path: string;
    name: string;
    previewUrl?: string; // base64 data URL
    width?: number;      // image width in pixels
    height?: number;     // image height in pixels
    isLoading?: boolean;
  }

  interface PdfResponse {
    success: boolean;
    error?: string;
    page_count?: number;
    file_size?: number;
  }

  const images = writable<ImageInfo[]>([]);
  let isProcessing = $state(false);
  let progress = $state(0);
  let statusMessage = $state('');
  let previewPageIndex = $state(0);
  
  // Conversion options
  let pageSize = $state<'A4' | 'Letter'>('A4');
  let orientation = $state<'auto' | 'portrait' | 'landscape'>('auto');
  let margin = $state(20);
  let quality = $state(85);
  let fitMode = $state<'contain' | 'cover' | 'stretch'>('contain');

  // Page dimensions in points (1 point = 1/72 inch)
  const pageSizes = {
    A4: { width: 595.28, height: 841.89 },
    Letter: { width: 612, height: 792 }
  };

  // Supported image formats and their MIME types
  const imageFormats: Record<string, string> = {
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'bmp': 'image/bmp',
    'tiff': 'image/tiff',
    'tif': 'image/tiff',
    'webp': 'image/webp',
    'gif': 'image/gif'
  };

  // Supported image formats for file dialog
  const imageFilters = [{
    name: 'Images',
    extensions: Object.keys(imageFormats)
  }];

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  // Get MIME type from file extension
  function getMimeType(path: string): string {
    const ext = path.split('.').pop()?.toLowerCase() || '';
    return imageFormats[ext] || 'image/jpeg';
  }

  // Load image as base64 data URL using fs plugin
  async function loadImagePreview(imagePath: string): Promise<void> {
    try {
      // Set loading state
      images.update(imgs => imgs.map(item => 
        item.path === imagePath ? { ...item, isLoading: true } : item
      ));
      
      // Read file as Uint8Array using Tauri fs plugin
      const fileData = await readFile(imagePath);
      
      // Convert to base64
      const base64 = btoa(
        new Uint8Array(fileData).reduce(
          (data, byte) => data + String.fromCharCode(byte),
          ''
        )
      );
      
      // Create data URL
      const mimeType = getMimeType(imagePath);
      const previewUrl = `data:${mimeType};base64,${base64}`;
      
      // Get image dimensions by loading it in browser
      const imageLoader = new Image();
      imageLoader.onload = () => {
        // Update with loaded data - create new array to trigger reactivity
        images.update(imgs => imgs.map(item => 
          item.path === imagePath 
            ? { ...item, previewUrl, width: imageLoader.naturalWidth, height: imageLoader.naturalHeight, isLoading: false }
            : item
        ));
      };
      imageLoader.onerror = () => {
        images.update(imgs => imgs.map(item => 
          item.path === imagePath ? { ...item, isLoading: false } : item
        ));
      };
      imageLoader.src = previewUrl;
      
    } catch (err) {
      console.error('Failed to load image preview:', err);
      images.update(imgs => imgs.map(item => 
        item.path === imagePath ? { ...item, previewUrl: undefined, isLoading: false } : item
      ));
    }
  }

  // Get preview dimensions based on current settings AND current image dimensions
  function getPreviewDimensions(currentImage: ImageInfo | undefined) {
    let baseWidth = pageSizes[pageSize].width;
    let baseHeight = pageSizes[pageSize].height;
    
    // Determine actual orientation based on settings and image dimensions
    let actualLandscape = false;
    
    if (orientation === 'landscape') {
      // Force landscape
      actualLandscape = true;
    } else if (orientation === 'portrait') {
      // Force portrait
      actualLandscape = false;
    } else if (orientation === 'auto' && currentImage && currentImage.width && currentImage.height) {
      // Auto: match page orientation to image aspect ratio
      // If image is wider than tall, use landscape page
      actualLandscape = currentImage.width > currentImage.height;
    }
    
    // Apply orientation
    if (actualLandscape) {
      [baseWidth, baseHeight] = [baseHeight, baseWidth];
    }
    
    // Scale for display
    const maxDisplayWidth = 280;
    const maxDisplayHeight = 380;
    const scale = Math.min(maxDisplayWidth / baseWidth, maxDisplayHeight / baseHeight);
    
    const pageWidth = baseWidth * scale;
    const pageHeight = baseHeight * scale;
    const marginScaled = margin * scale;
    
    return {
      pageWidth,
      pageHeight,
      marginScaled,
      contentWidth: pageWidth - (marginScaled * 2),
      contentHeight: pageHeight - (marginScaled * 2),
      isLandscape: actualLandscape
    };
  }

  async function selectImages() {
    try {
      const selected = await open({
        multiple: true,
        filters: imageFilters
      });

      if (selected && Array.isArray(selected)) {
        images.update(current => {
          const newImages = [...current];
          for (const path of selected) {
            if (!newImages.find(f => f.path === path)) {
              const fileInfo: ImageInfo = {
                path,
                name: path.split(/[/\\]/).pop() || path,
                isLoading: true
              };
              newImages.push(fileInfo);
              loadImagePreview(path);
            }
          }
          return newImages;
        });
        previewPageIndex = 0;
      }
    } catch (err) {
      console.error('Failed to select images:', err);
      statusMessage = `选择图片失败: ${err}`;
    }
  }

  function removeImage(index: number) {
    images.update(current => {
      const newImages = current.filter((_, i) => i !== index);
      if (previewPageIndex >= newImages.length) {
        previewPageIndex = Math.max(0, newImages.length - 1);
      }
      return newImages;
    });
  }

  function moveUp(index: number) {
    if (index <= 0) return;
    images.update(current => {
      const newImages = [...current];
      [newImages[index - 1], newImages[index]] = [newImages[index], newImages[index - 1]];
      if (previewPageIndex === index) previewPageIndex--;
      else if (previewPageIndex === index - 1) previewPageIndex++;
      return newImages;
    });
  }

  function moveDown(index: number) {
    images.update(current => {
      if (index >= current.length - 1) return current;
      const newImages = [...current];
      [newImages[index], newImages[index + 1]] = [newImages[index + 1], newImages[index]];
      if (previewPageIndex === index) previewPageIndex++;
      else if (previewPageIndex === index + 1) previewPageIndex--;
      return newImages;
    });
  }

  function clearAll() {
    images.set([]);
    previewPageIndex = 0;
    statusMessage = '';
  }

  function generateDefaultConvertName(): string {
    let currentImages: ImageInfo[] = [];
    images.subscribe(i => currentImages = i)();
    
    if (currentImages.length === 0) {
      return 'images.pdf';
    }
    
    const firstName = currentImages[0].name;
    // Remove common image extensions
    const baseName = firstName.replace(/\.(jpg|jpeg|png|bmp|tiff?|gif|webp)$/i, '');
    return `${baseName}.pdf`;
  }


  async function convertToPdf() {
    let currentImages: ImageInfo[] = [];
    const unsub = images.subscribe(i => currentImages = i);

    if (currentImages.length === 0) {
      statusMessage = '请至少选择1张图片';
      unsub();
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
        defaultPath: generateDefaultConvertName()
      });
      
      if (!selected || typeof selected !== 'string') {
        unsub();
        return; // 用户取消
      }
      outputPath = selected;
    } catch (err) {
      console.error('Failed to select output path:', err);
      statusMessage = `选择输出路径失败: ${err}`;
      unsub();
      return;
    }

    isProcessing = true;
    progress = 0;
    statusMessage = '正在转换为PDF...';

    try {
      const imagePaths = currentImages.map(i => i.path);

      const options = {
        page_size: pageSize,
        orientation: orientation,
        margin: margin,
        quality: quality,
        fit: fitMode
      };

      const response = await invoke<PdfResponse>('pdf_convert_images', {
        images: imagePaths,
        output: outputPath,
        options: options
      });

      if (response.success) {
        progress = 100;
        const sizeStr = response.file_size ? formatFileSize(response.file_size) : '';
        statusMessage = `转换成功！共 ${response.page_count} 页${sizeStr ? `，文件大小 ${sizeStr}` : ''}`;
        images.set([]);
        previewPageIndex = 0;
      } else {
        statusMessage = `转换失败: ${response.error || '未知错误'}`;
      }
    } catch (err) {
      console.error('Conversion failed:', err);
      statusMessage = `转换失败: ${err}`;
    } finally {
      isProcessing = false;
      unsub();
      setTimeout(() => {
        statusMessage = '';
        progress = 0;
      }, 3000);
    }
  }
</script>

<div class="p-8">
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-800">图片转PDF</h1>
    <p class="text-gray-600 mt-2">将多张图片合并转换为一个PDF文件</p>
  </div>
  
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Left Column: Image List & Options -->
    <div>
      <!-- Image Selection -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-gray-700">已选择的图片</h2>
          <div class="flex gap-2">
            <button
              onclick={clearAll}
              disabled={$images.length === 0}
              class="px-3 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              清空
            </button>
            <button
              onclick={selectImages}
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              添加图片
            </button>
          </div>
        </div>
        
        {#if $images.length === 0}
          <div class="text-center py-12 text-gray-400">
            <svg class="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p>点击上方按钮添加图片文件</p>
            <p class="text-sm mt-2">支持 JPG, PNG, BMP, TIFF, WebP, GIF 格式</p>
          </div>
        {:else}
          <ul class="space-y-2 max-h-80 overflow-y-auto">
            {#each $images as image, index}
              <li
                class="flex items-center justify-between p-3 rounded-lg group bg-gray-50 hover:bg-gray-100 {previewPageIndex === index ? 'ring-2 ring-blue-500' : ''}"
              >
                <div class="flex items-center gap-3 flex-1 min-w-0">
                  <span class="text-gray-400 font-mono text-sm w-8 shrink-0">{index + 1}</span>

                  <!-- Image thumbnail -->
                  <button 
                    onclick={() => previewPageIndex = index}
                    class="w-14 h-14 shrink-0 flex items-center justify-center bg-gray-200 rounded overflow-hidden hover:ring-2 hover:ring-blue-400 transition-all"
                  >
                    {#if image.isLoading}
                      <svg class="w-6 h-6 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 9.373 0 012 4z"></path>
                      </svg>
                    {:else if image.previewUrl}
                      <img 
                        src={image.previewUrl} 
                        alt={image.name} 
                        class="w-full h-full object-cover"
                      />
                    {:else}
                      <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    {/if}
                  </button>

                  <div class="flex-1 min-w-0">
                    <span class="truncate text-gray-700 text-sm block" title={image.name}>{image.name}</span>
                    {#if image.width && image.height}
                      <span class="text-xs text-gray-400">{image.width} × {image.height}px · {image.width > image.height ? '横向' : image.width < image.height ? '纵向' : '方形'}</span>
                    {/if}
                  </div>
                </div>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
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
                    disabled={index === $images.length - 1}
                    class="p-1 text-gray-400 hover:text-blue-600 disabled:opacity-30 disabled:cursor-not-allowed"
                    title="下移"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  <div class="w-px h-5 bg-gray-300 mx-1"></div>
                  <button
                    onclick={() => removeImage(index)}
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
          <p class="text-xs text-gray-400 mt-2">点击缩略图可预览该图片的PDF效果</p>
        {/if}
      </div>
      
      <!-- Conversion Options -->
      <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
        <h2 class="text-lg font-semibold text-gray-700 mb-4">转换选项</h2>
        
        <div class="grid grid-cols-2 gap-6">
          <!-- Page Size -->
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">页面大小</label>
            <select 
              bind:value={pageSize}
              class="w-full px-3 py-2 border rounded-lg text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="A4">A4 (210 × 297 mm)</option>
              <option value="Letter">Letter (216 × 279 mm)</option>
            </select>
          </div>
          
          <!-- Orientation -->
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">页面方向</label>
            <select 
              bind:value={orientation}
              class="w-full px-3 py-2 border rounded-lg text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            >
              <option value="auto">自动（根据图片）</option>
              <option value="portrait">纵向</option>
              <option value="landscape">横向</option>
            </select>
          </div>
          
          <!-- Margin -->
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">边距: {margin}px</label>
            <input 
              type="range" 
              bind:value={margin}
              min="0"
              max="100"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
          
          <!-- Quality -->
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">图片质量: {quality}%</label>
            <input 
              type="range" 
              bind:value={quality}
              min="50"
              max="100"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            />
          </div>
        </div>
        
        <!-- Fit Mode -->
        <div class="mt-4">
          <label class="block text-sm font-medium text-gray-600 mb-2">适应模式</label>
          <div class="flex flex-wrap gap-4">
            <label class="flex items-center gap-2 cursor-pointer text-sm">
              <input type="radio" bind:group={fitMode} value="contain" class="w-4 h-4" />
              <span class="text-gray-700">适应（保持比例）</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer text-sm">
              <input type="radio" bind:group={fitMode} value="cover" class="w-4 h-4" />
              <span class="text-gray-700">填充（可能裁剪）</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer text-sm">
              <input type="radio" bind:group={fitMode} value="stretch" class="w-4 h-4" />
              <span class="text-gray-700">拉伸（填满页面）</span>
            </label>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Right Column: PDF Preview -->
    <div>
      <div class="bg-white rounded-lg shadow-sm p-6 sticky top-8">
        <h2 class="text-lg font-semibold text-gray-700 mb-4">
          PDF效果预览
          {#if $images.length > 0}
            <span class="text-sm font-normal text-gray-500">
              （第 {previewPageIndex + 1} 页，共 {$images.length} 页）
            </span>
          {/if}
        </h2>
        
        {#if $images.length === 0}
          <div class="text-center py-16 text-gray-400 bg-gray-50 rounded-lg">
            <svg class="w-20 h-20 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>添加图片后可预览PDF效果</p>
          </div>
        {:else}
          {@const currentImage = $images[previewPageIndex]}
          {@const dims = getPreviewDimensions(currentImage)}
          <!-- Page Preview -->
          <div class="flex justify-center items-center bg-gray-100 rounded-lg p-4 min-h-[450px]">
            <div 
              class="bg-white shadow-lg relative"
              style="width: {dims.pageWidth}px; height: {dims.pageHeight}px;"
            >
              <!-- Content area with margin -->
              {#if currentImage?.previewUrl && !currentImage.isLoading}
                <div 
                  class="absolute overflow-hidden bg-gray-50"
                  style="left: {dims.marginScaled}px; top: {dims.marginScaled}px; width: {dims.contentWidth}px; height: {dims.contentHeight}px;"
                >
                  <img 
                    src={currentImage.previewUrl}
                    alt="Preview"
                    class="w-full h-full"
                    style="object-fit: {fitMode === 'contain' ? 'contain' : fitMode === 'cover' ? 'cover' : 'fill'};"
                  />
                </div>
              {:else if currentImage?.isLoading}
                <div 
                  class="absolute flex items-center justify-center bg-gray-50"
                  style="left: {dims.marginScaled}px; top: {dims.marginScaled}px; width: {dims.contentWidth}px; height: {dims.contentHeight}px;"
                >
                  <svg class="w-8 h-8 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 9.373 0 012 4z"></path>
                  </svg>
                </div>
              {/if}
              
              <!-- Page label -->
              <div class="absolute bottom-2 right-2 text-xs text-gray-400 bg-white bg-opacity-80 px-2 py-1 rounded">
                {pageSize} · {dims.isLandscape ? '横向' : '纵向'}
              </div>
            </div>
          </div>
          
          <!-- Page navigation -->
          {#if $images.length > 1}
            <div class="flex justify-center items-center gap-4 mt-4">
              <button
                onclick={() => previewPageIndex = Math.max(0, previewPageIndex - 1)}
                disabled={previewPageIndex === 0}
                class="px-3 py-1 text-gray-600 border rounded hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                上一页
              </button>
              <span class="text-sm text-gray-600">
                {previewPageIndex + 1} / {$images.length}
              </span>
              <button
                onclick={() => previewPageIndex = Math.min($images.length - 1, previewPageIndex + 1)}
                disabled={previewPageIndex === $images.length - 1}
                class="px-3 py-1 text-gray-600 border rounded hover:bg-gray-50 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                下一页
              </button>
            </div>
          {/if}
          
          <!-- Preview info -->
          <div class="mt-4 text-xs text-gray-500 space-y-1">
            {#if currentImage?.width && currentImage?.height}
              <p>• 图片尺寸: {currentImage.width} × {currentImage.height}px ({currentImage.width > currentImage.height ? '横向图片' : currentImage.width < currentImage.height ? '纵向图片' : '方形图片'})</p>
            {/if}
            <p>• 页面方向: {orientation === 'auto' ? '自动' : orientation === 'portrait' ? '强制纵向' : '强制横向'} → {dims.isLandscape ? '横向页面' : '纵向页面'}</p>
            <p>• 适应模式: {fitMode === 'contain' ? '保持图片比例，完整显示' : fitMode === 'cover' ? '填充页面，可能裁剪图片' : '拉伸图片填满页面'}</p>
          </div>
        {/if}
      </div>
    </div>
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
      onclick={convertToPdf}
      disabled={$images.length === 0 || isProcessing}
      class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      开始转换
    </button>
    <span class="text-sm text-gray-500">
      {$images.length} 张图片已选择
    </span>
  </div>
</div>
