# Frontend AGENTS.md

**范围:** SvelteKit 前端 (src/)

## OVERVIEW

Tauri 桌面 PDF 编辑器的前端，采用 SvelteKit + TypeScript + TailwindCSS v4。禁用 SSR，所有页面作为 SPA 加载。通过 Tauri IPC 与 Rust 后端通信，Rust 再转发到 Python sidecar 执行 PDF 操作。

## STRUCTURE

```
src/
├── lib/
│   ├── types.ts           # TypeScript 接口定义
│   └── components/
│       └── Layout/
│           └── Sidebar.svelte
├── routes/
│   ├── +layout.svelte     # 根布局，含 Sidebar
│   ├── +layout.ts         # ssr = false 配置
│   ├── +page.svelte       # PDF 合并页面 (/)
│   └── split/
│       └── +page.svelte   # PDF 拆分页面 (/split)
└── app.css                # Tailwind 全局导入
```

## WHERE TO LOOK

| 任务 | 位置 | 说明 |
|------|------|------|
| 新增页面 | `src/routes/` | 创建 `+page.svelte` 文件 |
| 类型定义 | `src/lib/types.ts` | FileEntry, SplitMode 等接口 |
| 布局组件 | `src/lib/components/Layout/Sidebar.svelte` | 侧边栏导航 |
| Tauri 调用 | 各 `+page.svelte` | 使用 `import { invoke } from '@tauri-apps/api/core'` |
| 弹窗选择 | `@tauri-apps/plugin-dialog` | `open()`, `save()` 函数 |
| 缩略图预览 | `pdf_get_thumbnails`, `pdf_get_file_preview` | 返回 base64 PNG 图片 |

## CONVENTIONS

- **路由**: 文件路由 `src/routes/子目录/+page.svelte` → `/子目录`
- **响应式**: Svelte 5 runes，`let count = $state(0)`，`let { children } = $props()`
- **样式**: Tailwind 类直接写在 HTML 上，无 CSS 模块
- **导入**: 使用 `$lib/` 别名导入 `src/lib/` 下的模块
- **UI 语言**: 中文界面，所有页面文本使用简体中文
- **SSR**: `src/routes/+layout.ts` 设置 `ssr = false`
- **缩略图**: 使用 `data:image/png;base64,{image}` 格式显示

## INCOMPLETE

- `/convert` 路由未创建 (图片转 PDF)
- `/edit` 路由未创建 (文本编辑)
- 合并页面预览缩略图未显示 (需调试)
- 分拆页面缩略图显示为黑色 (需调试)
