<script lang="ts">
  const navItems = [
    { path: '/', label: 'PDF合并', icon: 'merge' },
    { path: '/split', label: 'PDF分拆', icon: 'split' },
    { path: '/convert', label: '图片转PDF', icon: 'image' },
    { path: '/edit', label: '文字编辑', icon: 'edit' }
  ];
  
  let currentPath = $state('/');
</script>

<aside class="w-64 bg-white border-r border-gray-200 flex flex-col h-screen">
  <!-- Logo -->
  <div class="p-6 border-b border-gray-200">
    <h1 class="text-xl font-bold text-gray-800 flex items-center gap-2">
      <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2m8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 00-2-2v10a2 2 0 002 2h8a2 2 0 012-2.586 1 1 0 01.707.293l4.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      PDF编辑器
    </h1>
    <p class="text-xs text-gray-500 mt-1">v0.1.0</p>
  </div>
  
  <!-- Navigation -->
  <nav class="flex-1 py-4">
    <ul class="space-y-1 px-3">
      {#each navItems as item}
        <li>
        <a 
          href={item.path}
          onclick={() => currentPath = item.path}
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-color {currentPath === item.path 
            ? 'bg-blue-50 text-blue-700 font-medium' 
            : 'text-gray-600 hover:bg-gray-50'}"
        >
          {#if item.icon === 'merge'}
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
            </svg>
          {:else if item.icon === 'split'}
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5-5M4 16v4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5-5" />
            </svg>
          {:else if item.icon === 'image'}
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L1 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2v-5.586-4.586a2 2 0 012.828 0L8 8H.01M8 8h.01M12 12h8a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v.5h.5a.5.5 0 01.5.5v3a2 2 0 01-2 2z" />
            </svg>
          {:else if item.icon === 'edit'}
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          {/if}
          <span>{item.label}</span>
        </a>
      </li>
    {/each}
  </ul>
  </nav>
  
  <!-- Footer -->
  <div class="p-4 border-t border-gray-200">
    <p class="text-xs text-gray-400 text-center">
      © 2026 PDF Editor
    </p>
  </div>
</aside>
