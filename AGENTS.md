# PDF Editor - Project Knowledge Base

**Generated:** 2026-03-08
**Stack:** Tauri 2.x + SvelteKit 2.x + TypeScript 5.x + Python 3.11+

---

## OVERVIEW

Windows desktop PDF editor with merge, split, image-to-PDF, and text editing capabilities. Uses Tauri for native desktop application, SvelteKit for frontend UI, and Python sidecar (PyMuPDF) for PDF operations.

**Core Goal:** 提供简单易用的PDF处理工具，支持合并、分拆、图片转PDF、文字编辑四大核心功能，所有操作本地完成，无需联网。

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend Layer (WebView)                      │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  SvelteKit 2.x + TypeScript 5.x + TailwindCSS v4           ││
│  │  ┌─────────┬─────────┬──────────┬─────────┐                ││
│  │  │ PDF合并 │ PDF分拆 │ 图片转PDF │ 文字编辑│                ││
│  │  │   ✅    │   ✅    │   ⚠️后端  │   ⚠️后端 │                ││
│  │  └─────────┴─────────┴──────────┴─────────┘                ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                           ↕ Tauri IPC (invoke/events)
┌─────────────────────────────────────────────────────────────────┐
│                  Backend Layer (Rust Main Process)               │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Tauri 2.x Plugins: dialog, fs, shell                       ││
│  │  Commands: pdf_merge, pdf_split, pdf_convert_images, etc.   ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                           ↕ stdio (JSON-RPC 2.0)
┌─────────────────────────────────────────────────────────────────┐
│               PDF Processing Layer (Python Sidecar)              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  PyMuPDF 1.24+ (fitz) - PDF Operations                       ││
│  │  Handlers: merge, split, convert, edit, thumbnails          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## STRUCTURE

```
pdf-editor/
├── src/                    # SvelteKit frontend
│   ├── lib/
│   │   ├── types.ts           # TypeScript interfaces
│   │   └── components/
│   │       └── Layout/
│   │           └── Sidebar.svelte
│   └── routes/
│       ├── +layout.svelte     # Root layout with sidebar
│       ├── +page.svelte       # PDF合并 (/)
│       └── split/
│           └── +page.svelte   # PDF分拆 (/split)
├── src-tauri/              # Rust backend
│   ├── src/
│   │   ├── main.rs            # Entry point
│   │   ├── lib.rs             # Tauri commands
│   │   └── sidecar/mod.rs     # JSON-RPC client
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   └── capabilities/default.json
├── pdf-sidecar/            # Python PDF processor
│   ├── src/
│   │   ├── __main__.py        # JSON-RPC server entry
│   │   ├── core/pdf_ops.py    # Utilities
│   │   ├── handlers/
│   │   │   ├── merge.py       # pdf.merge
│   │   │   ├── split.py       # pdf.split
│   │   │   ├── convert.py     # pdf.convert_images
│   │   │   ├── edit.py        # pdf.edit_text
│   │   │   └── thumbnails.py  # pdf.get_thumbnails, pdf.get_file_preview
│   │   └── utils/temp.py
│   └── requirements.txt
└── static/
```

---

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new PDF operation | `pdf-sidecar/src/handlers/` | Create handler, register in `__main__.py` |
| Add new UI page | `src/routes/` | File-based routing, create `+page.svelte` |
| Add Tauri command | `src-tauri/src/lib.rs` | Use `#[tauri::command]` attribute |
| Connect UI to backend | `src/routes/*.svelte` | Use `invoke()` from `@tauri-apps/api/core` |
| Shared types | `src/lib/types.ts` | TypeScript interfaces for PDF operations |
| Sidecar communication | `src-tauri/src/sidecar/mod.rs` | JSON-RPC client |
| Thumbnail generation | `pdf-sidecar/src/handlers/thumbnails.py` | `pdf.get_thumbnails`, `pdf.get_file_preview` |

---

## API REFERENCE

### Python Handlers (JSON-RPC Methods)

| Method | Handler | Status | Description |
|--------|---------|--------|-------------|
| `pdf.merge` | merge.py | ✅ Complete | Merge multiple PDFs |
| `pdf.split` | split.py | ⚠️ Partial | Split PDF (bookmark mode not implemented) |
| `pdf.convert_images` | convert.py | ✅ Complete | Convert images to PDF |
| `pdf.edit_text` | edit.py | ✅ Complete | Edit text in PDF |
| `pdf.get_thumbnails` | thumbnails.py | ✅ Complete | Generate page thumbnails |
| `pdf.get_file_preview` | thumbnails.py | ✅ Complete | Generate first page preview |
| `system.ping` | __main__.py | ✅ Complete | Health check |
| `system.info` | __main__.py | ✅ Complete | System information |

### Tauri Commands (IPC Interface)

| Command | Parameters | Returns | Sidecar Method |
|---------|------------|---------|----------------|
| `pdf_merge` | files, output | PdfResponse | pdf.merge |
| `pdf_split` | file, output_dir, mode, options | PdfResponse | pdf.split |
| `pdf_convert_images` | images, output, options | PdfResponse | pdf.convert_images |
| `pdf_edit_text` | file, output, operations | PdfResponse | pdf.edit_text |
| `pdf_get_thumbnails` | file, max_pages, zoom | ThumbnailsResponse | pdf.get_thumbnails |
| `pdf_get_file_preview` | file, zoom | FilePreviewResponse | pdf.get_file_preview |
| `test_sidecar` | - | String | system.ping |

### Response Format Standard

All handlers return consistent response format:
```typescript
// Success
{ success: true, ...data }

// Error
{ success: false, error: "Error message string" }
```

---

## CONVENTIONS

### Frontend (SvelteKit)
- **Svelte 5 runes**: Use `$state()` for reactive state, `$props()` for component props
- **SSR disabled**: `src/routes/+layout.ts` sets `ssr = false`
- **UI Language**: 中文界面
- **Styling**: TailwindCSS v4 inline classes
- **Routing**: File-based routing in `src/routes/`

### Backend (Rust/Tauri)
- **Commands**: Return `Result<T, String>` with `map_err()` for context
- **Error propagation**: Sidecar → JSON-RPC error → Rust error → Frontend catch
- **Plugins**: dialog 2.6.0, fs 2.4.5, shell 2.3.5

### Python Sidecar
- **Response format**: `{'success': bool, ...}` or `{'success': False, 'error': str}`
- **Page indexing**: 1-indexed in params, 0-indexed for PyMuPDF (fitz)
- **Logging**: `logging.getLogger(__name__)` to stderr
- **Method naming**: `pdf.merge`, `pdf.split`, etc.
- **Windows path handling**: Use `sys.stdin.buffer` with UTF-8 decode

---

## IMPLEMENTATION STATUS

### ✅ Completed Features

| Feature | Frontend | Backend | Notes |
|---------|----------|---------|-------|
| PDF合并 | ✅ +page.svelte | ✅ merge.py | Full functionality with preview |
| PDF分拆 | ✅ split/+page.svelte | ✅ split.py | Range, fixed, extract modes |
| 图片转PDF | ❌ Missing page | ✅ convert.py | Backend ready, UI not created |
| 文字编辑 | ❌ Missing page | ✅ edit.py | Backend ready, UI not created |
| 缩略图预览 | ⚠️ Debug needed | ✅ thumbnails.py | Runtime issues |

### ⚠️ Incomplete Features

| Issue | Location | Priority | Description |
|-------|----------|----------|-------------|
| 书签分拆未实现 | split.py:97 | High | `mode='bookmark'` returns error |
| /convert 路由缺失 | src/routes/ | High | Image to PDF page not created |
| /edit 路由缺失 | src/routes/ | High | Text editing page not created |
| 合并页缩略图不显示 | +page.svelte | Medium | Preview not rendering at runtime |
| 分拆页缩略图黑色 | split/+page.svelte | Medium | Thumbnails showing black |

### 🔴 Code Issues

| Issue | Location | Impact |
|-------|----------|--------|
| 语法错误 | temp.py:12 | Extra closing parenthesis |
| 孤立except块 | temp.py:20-21 | No matching try block |

---

## VERIFICATION STANDARDS (验收标准)

### PDF合并
- ✅ 支持至少合并20个PDF文件
- ⚠️ 合并后文件大小不超过源文件总和的110% (待验证)
- ✅ 合并后页面顺序与用户设定一致
- ⚠️ 100页以内文件合并时间不超过5秒 (待验证)

### PDF分拆
- ✅ 支持按页码范围分拆
- ✅ 支持按固定页数分拆
- ✅ 支持提取特定页面
- ❌ 支持按书签分拆 (未实现)
- ⚠️ 支持至少1000页的PDF文件 (待验证)
- ⚠️ 分拆速度：10页/秒 (待验证)

### 图片转PDF
- ⚠️ 支持常见图片格式：JPG, PNG, BMP, TIFF (后端已实现)
- ⚠️ 支持至少50张图片合并 (后端已实现)
- ❌ 支持拖拽导入 (UI未实现)
- ❌ 支持EXIF自动旋转 (后端已实现，UI未实现)

### 文字编辑
- ⚠️ 支持替换文字 (后端已实现)
- ⚠️ 支持添加文字 (后端已实现)
- ⚠️ 支持删除文字 (后端已实现)
- ❌ 支持富文本编辑 (未实现)

---

## COMMANDS

```bash
# Development
pnpm dev              # Start Vite dev server (port 1420)
pnpm tauri dev        # Dev with Tauri desktop app

# Build
pnpm build            # Build frontend
pnpm tauri build      # Production build

# Type checking
pnpm check            # svelte-kit sync + svelte-check

# Windows fix
npm install @tauri-apps/cli-win32-x64-msvc --no-save
```

---

## ANTI-PATTERNS

- **DO NOT** remove `#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]` in main.rs
- **DO NOT** enable SSR (Tauri has no Node.js server)
- **DO NOT** use npm/yarn (project uses pnpm)
- **NEVER** suppress TypeScript errors with `as any` or `@ts-ignore`
- **DO NOT** remove source file line prefixes (e.g., `#QB|`)

---

## KNOWN ISSUES

| Issue | Status | Notes |
|-------|--------|-------|
| 命名不一致 | ⚠️ Open | `pdf_editor` vs `pdf_editor_temp` |
| CSP已禁用 | ⚠️ Security | `"csp": null` in tauri.conf.json |
| PyMuPDF AGPL-3.0 | ⚠️ Legal | License compatibility check needed |
| Sidecar未打包 | ⚠️ Config | Missing `externalBin` config |
| 无测试框架 | ℹ️ Info | No unit/integration tests |
| 无CI/CD | ℹ️ Info | Manual builds only |

---

## TECH STACK VERSIONS

| Component | Version | Notes |
|-----------|---------|-------|
| Tauri | 2.x | Latest stable |
| Svelte | 5.0.0 | With runes |
| SvelteKit | 2.9.0 | Static adapter |
| TypeScript | 5.6.2 | Strict mode |
| TailwindCSS | 4.2.1 | V4 syntax |
| Vite | 6.0.3 | Build tool |
| Python | 3.11+ | Sidecar runtime |
| PyMuPDF | >=1.24.0 | PDF operations |
| Pillow | >=11.0.0 | Image processing |
| Rust | Edition 2021 | Backend |

---

## ERROR HANDLING PATTERN

```
User Action
    ↓
[Svelte] try/catch → invoke<TauriCommand>()
    ↓
[Rust] Result<T, String> → call_sidecar() → map_err() for context
    ↓
[Python Server] try/catch → logger.exception() → {success: false, error: str}
    ↓
Error propagates back through layers with context at each level
```

**Key Conventions:**
- All responses have `success: boolean` field
- Errors always have `error: string` field (no error codes)
- Frontend displays `response.error || 'Unknown error'`
- Full stack traces logged to stderr in Python
