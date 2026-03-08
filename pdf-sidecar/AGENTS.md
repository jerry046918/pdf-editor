# PDF Sidecar - AGENTS.md

**Generated:** 2026-03-08

## OVERVIEW

Python JSON-RPC 2.0 server handling PDF operations for the Tauri desktop app. Uses PyMuPDF (fitz) for PDF manipulation and communicates with Rust via stdio.

## STRUCTURE

```
pdf-sidecar/
├── src/
│   ├── __main__.py        # JSON-RPC server entry, main() registers handlers
│   ├── core/
│   │   └── pdf_ops.py     # Utilities: get_page_count, get_toc, render_page
│   ├── handlers/
│   │   ├── merge.py       # pdf.merge
│   │   ├── split.py       # pdf.split (range/fixed/extract/bookmark)
│   │   ├── convert.py     # pdf.convert_images
│   │   ├── edit.py        # pdf.edit_text
│   │   └── thumbnails.py  # pdf.get_thumbnails, pdf.get_file_preview
│   └── utils/temp.py      # Temporary file management
└── requirements.txt       # PyMuPDF>=1.24.0, Pillow>=11.0.0
```

## WHERE TO LOOK

| Task | Location |
|------|----------|
| Add new PDF operation | `handlers/*.py` (create handler, register in `__main__.py`) |
| Debug JSON-RPC | `__main__.py` JSONRPCServer class |
| Core utilities | `core/pdf_ops.py` |
| Thumbnail generation | `handlers/thumbnails.py` |
| Response format | Any handler returns `{'success': bool, ...}` or `{'success': False, 'error': str}` |

## JSON-RPC METHODS

| Method | Handler | Purpose |
|--------|---------|---------|
| `pdf.merge` | merge.py | Merge multiple PDFs |
| `pdf.split` | split.py | Split PDF (range/fixed/extract/bookmark) |
| `pdf.convert_images` | convert.py | Convert images to PDF |
| `pdf.edit_text` | edit.py | Edit text in PDF |
| `pdf.get_thumbnails` | thumbnails.py | Generate page thumbnails |
| `pdf.get_file_preview` | thumbnails.py | Generate first page preview |
| `system.ping` | __main__.py | Health check |
| `system.info` | __main__.py | System information |

## HANDLER PATTERN

```python
# handlers/example.py
import fitz
import logging

logger = logging.getLogger(__name__)

def handler_func(params: dict) -> dict:
    file_path = params.get('file')
    if not file_path:
        return {'success': False, 'error': 'Missing file'}
    
    try:
        doc = fitz.open(file_path)
        return {'success': True, 'page_count': len(doc)}
    except Exception as e:
        logger.exception("Handler failed")
        return {'success': False, 'error': str(e)}

def register(server):
    server.register_method('pdf.example', handler_func)
```

Register in `__main__.py` main(): `from src.handlers import example; example.register(server)`

## CONVENTIONS

- Use `fitz` (PyMuPDF) for PDF ops
- Return `{'success': True, ...}` or `{'success': False, 'error': str}`
- Page indexing: 1-indexed in params, 0-indexed for fitz
- Logging: `logger = logging.getLogger(__name__)` to stderr, use `logger.exception()` for errors
- Method names: `pdf.merge`, `pdf.split`, `pdf.get_thumbnails`, `pdf.get_file_preview`
- **Windows path encoding**: Use `sys.stdin.buffer` and decode UTF-8 to handle Chinese paths

## INCOMPLETE

- `handlers/split.py:97` - Bookmark splitting not implemented (mode='bookmark' returns error)
