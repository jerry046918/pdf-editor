"""PDF Merge Handler"""

import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def merge_pdfs(params: dict) -> dict:
    """
    Merge multiple PDF files into one.
    
    Args:
        params: {
            'files': list[str],  # PDF file paths
            'output': str,       # Output path
            'options': {
                'pages': Optional[list[list[int]]],  # Page ranges per file
                'preserve_bookmarks': bool
            }
        }
    
    Returns:
        {'success': bool, 'page_count': int, 'file_size': int, 'error': Optional[str]}
    """
    files = params.get('files', [])
    output_path = params.get('output')
    options = params.get('options', {})
    
    if not files:
        return {'success': False, 'error': 'No files provided'}
    
    if not output_path:
        return {'success': False, 'error': 'No output path provided'}
    
    try:
        result = fitz.open()
        total_pages = 0
        
        for i, file_path in enumerate(files):
            logger.info(f"Merging file {i+1}/{len(files)}: {file_path}")
            
            src = fitz.open(file_path)
            pages_range = options.get('pages', [None])[i] if options.get('pages') else None
            
            if pages_range:
                # Insert specific page range (convert 1-indexed to 0-indexed)
                start = pages_range[0] - 1 if pages_range[0] > 0 else 0
                end = pages_range[1] - 1 if len(pages_range) > 1 else src.page_count - 1
                result.insert_pdf(src, from_page=start, to_page=end)
            else:
                # Insert all pages
                result.insert_pdf(src)
            
            total_pages += src.page_count
            src.close()
        
        # Save result
        result.save(output_path)
        file_size = Path(output_path).stat().st_size
        
        logger.info(f"Merge complete: {total_pages} pages, {file_size} bytes")
        
        return {
            'success': True,
            'page_count': len(result),
            'file_size': file_size
        }
        
    except Exception as e:
        logger.exception("Error merging PDFs")
        return {'success': False, 'error': str(e)}


def register(server):
    """Register merge methods with the server"""
    server.register_method('pdf.merge', merge_pdfs)
    logger.info("PDF merge handler registered")
