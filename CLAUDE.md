# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF Editor is a Windows desktop application for PDF manipulation built with a three-layer architecture:
- **Frontend**: SvelteKit 5 + TypeScript + TailwindCSS v4
- **Backend**: Tauri 2.x (Rust)
- **PDF Processing**: Python sidecar (PyMuPDF) via JSON-RPC over stdio

## Development Commands

```bash
# Development
pnpm dev              # Start frontend dev server (port 1420)
pnpm tauri dev        # Launch Tauri desktop app in dev mode

# Building
pnpm build            # Build frontend only
pnpm tauri build      # Build production desktop app (.exe)

# Type checking
pnpm check            # Run svelte-check

# Python sidecar (requires Python 3.11+)
pip install -r pdf-sidecar/requirements.txt
```

## Architecture

```
Frontend (WebView)                    Rust (Main Process)              Python Sidecar
┌─────────────────────┐               ┌──────────────────┐            ┌──────────────┐
│ SvelteKit Routes    │               │ Tauri Commands   │            │ JSON-RPC     │
│ / (merge)           │  invoke()     │ pdf_merge()      │  stdio     │ pdf.merge    │
│ /split              │ ───────────►  │ pdf_split()      │ ────────►  │ pdf.split    │
│ /convert            │               │ pdf_batch_split()│  JSON      │ pdf.batch_...│
│ /edit               │               │                  │            │              │
└─────────────────────┘               └──────────────────┘            └──────────────┘
```

### Key Files

| Layer | Path | Purpose |
|-------|------|---------|
| Frontend | `src/routes/*/+page.svelte` | Page components |
| Frontend | `src/lib/types.ts` | TypeScript interfaces |
| Rust | `src-tauri/src/lib.rs` | Tauri command definitions |
| Rust | `src-tauri/src/sidecar/mod.rs` | JSON-RPC client, sidecar lifecycle |
| Python | `pdf-sidecar/src/__main__.py` | JSON-RPC server entry point |
| Python | `pdf-sidecar/src/handlers/*.py` | PDF operation handlers |

### Data Flow

1. Frontend calls `invoke('pdf_merge', { files, output })` via Tauri API
2. Rust command in `lib.rs` wraps params and calls `call_sidecar("pdf.merge", params)`
3. SidecarManager sends JSON-RPC request to Python process via stdin
4. Python handler processes and returns result via stdout
5. Response propagates back: Python → Rust → Frontend

## Code Patterns

### Frontend (Svelte 5)
- Use `$state()` for reactive state (Runes API)
- Use `$effect()` for reactive side effects (NOT `$:` syntax)
- SSR is disabled (`ssr = false` in `+layout.ts`)
- UI language is Chinese
- TailwindCSS v4 inline classes

### Rust (Tauri Commands)
- All commands return `Result<T, String>`
- Use `serde_json::json!({})` to build params
- Parse responses with `serde_json::from_value()`

### Python Handlers
- Each handler file exports `register(server)` function
- Handlers return `{'success': bool, ...}` or `{'success': False, 'error': str}`
- Page indices in parameters are 1-based; convert to 0-based for PyMuPDF
- **IMPORTANT**: Use `with fitz.open()` context manager to ensure proper resource cleanup
- Use `logging.getLogger(__name__)` for logging (goes to stderr)

Example handler pattern:
```python
def some_operation(params: dict) -> dict:
    try:
        with fitz.open(file_path) as doc:
            # process document
            return {'success': True, 'result': ...}
    except Exception as e:
        logger.exception("Error description")
        return {'success': False, 'error': str(e)}
```

### Adding a New PDF Operation

1. Create handler in `pdf-sidecar/src/handlers/new_op.py`:
```python
def new_op(params: dict) -> dict:
    # Implementation
    return {'success': True, 'result': ...}

def register(server):
    server.register_method('pdf.new_op', new_op)
```

2. Import and register in `pdf-sidecar/src/__main__.py`

3. Add Tauri command in `src-tauri/src/lib.rs`:
```rust
#[tauri::command]
fn pdf_new_op(/* params */) -> Result<Response, String> {
    let result = call_sidecar("pdf.new_op", params)?;
    // parse and return
}
```

4. Register in `invoke_handler![]` macro

5. Call from frontend via `invoke('pdf_new_op', {...})`

## Production Build

The sidecar is bundled as an external binary. In production:
- Sidecar executable: `binaries/pdf-sidecar-x86_64-pc-windows-msvc.exe`
- Located via `get_sidecar_path()` in `sidecar/mod.rs`

The sidecar process is persistent (started once, reused for all operations) for performance.

## Security Notes

- CSP is enabled in `tauri.conf.json`
- File paths come from Tauri dialog plugin (user-selected files)
- Input validation is performed in both frontend and backend layers
