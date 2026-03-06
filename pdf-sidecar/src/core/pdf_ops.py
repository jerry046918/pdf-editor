"""Core Package - PDF Operations"""

import fitz  # PyMuPDF
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_page_count(file_path: str) -> dict:
    """Get page count of a PDF file"""
    try:
        doc = fitz.open(file_path)
        return {'success': True, 'page_count': doc.page_count}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_page_info(params: dict) -> dict:
    """Get information about a specific page"""
    file_path = params.get('file')
    page_num = params.get('page', 1) - 1  # Convert to 0-indexed
    
    if not file_path:
        return {'success': False, 'error': 'No file provided'}
    
    try:
        doc = fitz.open(file_path)
        if page_num < 0 or page_num >= doc.page_count:
            return {'success': False, 'error': 'Invalid page number'}
        
        page = doc[page_num]
        
        # Get page dimensions
        rect = page.rect
        
        return {
            'success': True,
            'width': rect.width,
            'height': rect.height,
            'rotation': page.rotation
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_toc(params: dict) -> dict:
    """Get table of contents from PDF"""
    file_path = params.get('file')
    
    if not file_path:
        return {'success': False, 'error': 'No file provided'}
    
    try:
        doc = fitz.open(file_path)
        toc = doc.get_toc()
        
        items = []
        for item in toc:
            items.append({
                'level': item[0],
                'title': item[1],
                'page': item[2] + 1  # Convert to 1-indexed
            })
        
        return {'success': True, 'toc': items}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def render_page(params: dict) -> dict:
    """Render a page to image (for preview)"""
    file_path = params.get('file')
    page_num = params.get('page', 0)
    zoom = params.get('zoom', 1.0)
    
    if not file_path:
        return {'success': False, 'error': 'No file provided'}
    
    try:
        doc = fitz.open(file_path)
        if page_num < 0 or page_num >= doc.page_count:
            return {'success': False, 'error': 'Invalid page number'}
        
        page = doc[page_num]
        
        # Render page to image
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # Return as base64
        import base64
        img_bytes = pix.tobytes()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return {
            'success': True,
            'image': img_base64,
            'width': pix.width,
            'height': pix.height
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}
