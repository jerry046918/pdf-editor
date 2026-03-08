# PDF Editor - Tauri Backend

**Generated:** 2026-03-08

## OVERVIEW

Tauri 2.x Rust backend for a Windows desktop PDF editor. Manages native window, filesystem access, and communicates with a Python sidecar process via JSON-RPC for PDF operations.

## STRUCTURE

```
src-tauri/
├── src/
│   ├── main.rs            # Binary entry (delegates to lib::run())
│   ├── lib.rs             # Tauri builder, plugin init, command handlers
│   └── sidecar/
│       └── mod.rs         # PdfSidecar client for Python JSON-RPC
├── capabilities/
│   └── default.json       # Tauri permissions (dialog, fs, shell)
├── Cargo.toml             # Dependencies (tauri 2, plugins, serde)
├── tauri.conf.json        # App config (port 1420, window settings)
└── build.rs               # Tauri build script
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add Tauri command | `src/lib.rs` | Use `#[tauri::command]` attribute |
| Plugin setup | `src/lib.rs` | dialog, fs, shell plugin initialization |
| Sidecar client | `src/sidecar/mod.rs` | JSON-RPC client, stdin/stdout communication |
| Permissions | `capabilities/default.json` | Add plugin permissions here |
| App window config | `tauri.conf.json` | Size, title, dev server port |

## TAURI COMMANDS (lib.rs)

| Command | Params | Returns |
|---------|--------|--------|
| `pdf_merge` | files, output | PdfResponse |
| `pdf_split` | file, output_dir, mode, options | PdfResponse |
| `pdf_convert_images` | images, output, options | PdfResponse |
| `pdf_edit_text` | file, output, operations | PdfResponse |
| `pdf_get_thumbnails` | file, max_pages, zoom | ThumbnailsResponse |
| `pdf_get_file_preview` | file, zoom | FilePreviewResponse |
| `test_sidecar` | - | String (ping result) |

## CONVENTIONS

- **Library name**: `pdf_editor_temp_lib` (Windows DLL conflict workaround)
- **Binary entry**: `main.rs` calls `pdf_editor_temp_lib::run()`
| **Plugin versions**: dialog 2.6.0, fs 2.4.5, shell 2.3.5
- **Dev port**: 1420 (hardcoded in tauri.conf.json)
- **Sidecar communication**: JSON-RPC 2.0 over stdin/stdout
- **Thread safety**: `Arc<Mutex<ChildStdin>>` for shared sidecar access

## INCOMPLETE

1. No `externalBin` config for bundling pdf-sidecar with the app.
2. Bookmark splitting in Python handler not implemented.

## ANTI-PATTERNS

- DO NOT remove `#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]` in main.rs
- DO NOT use `std::process::Command` directly for sidecar (breaks Tauri sandbox)
- DO NOT hardcode paths (use Tauri APIs for app data directories)
