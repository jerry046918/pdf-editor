"""PDF Thumbnail Handler - Generate thumbnails for preview"""

import fitz
import logging
import base64
from typing import List, Dict

logger = logging.getLogger(__name__)


def get_thumbnails(params: dict) -> dict:
    """
    Generate thumbnails for all pages in a PDF file.
    
    Args:
        params: {
            'file': str,           # PDF file path
            'max_pages': int,      # Optional: max pages to render (default: 50)
            'zoom': float          # Optional: zoom factor (default: 0.3 for thumbnails)
        }
    
    Returns:
        {
            'success': bool,
            'thumbnails': [
                {
                    'page': int,          # Page number (1-indexed)
                    'image': str,         # Base64 encoded PNG
                    'width': int,
                    'height': int
                }
            ],
            'total_pages': int,
            'error': Optional[str]
        }
    """
    file_path = params.get('file')
    max_pages = params.get('max_pages', 50)
    zoom = params.get('zoom', 0.3)
    
    if not file_path:
        return {'success': False, 'error': 'No file provided'}
    
    try:
        with fitz.open(file_path) as doc:
            total_pages = doc.page_count
            thumbnails = []

            pages_to_render = min(total_pages, max_pages)
            logger.info(f"Generating thumbnails for {file_path}: {pages_to_render} pages")

            mat = fitz.Matrix(zoom, zoom)

            for page_num in range(pages_to_render):
                page = doc[page_num]
                pix = page.get_pixmap(matrix=mat)

                img_bytes = pix.tobytes("png")
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')

                thumbnails.append({
                    'page': page_num + 1,  # 1-indexed
                    'image': img_base64,
                    'width': pix.width,
                    'height': pix.height
                })

                logger.debug(f"Generated thumbnail for page {page_num + 1}")

            logger.info(f"Generated {len(thumbnails)} thumbnails")

            return {
                'success': True,
                'thumbnails': thumbnails,
                'total_pages': total_pages
            }

    except Exception as e:
        logger.exception("Error generating thumbnails")
        return {'success': False, 'error': str(e)}


def get_file_preview(params: dict) -> dict:
    """
    Generate a preview for a PDF file (first page only).

    Args:
        params: {
            'file': str,           # PDF file path
            'zoom': float          # Optional: zoom factor (default: 0.5)
        }

    Returns:
        {
            'success': bool,
            'image': str,           # Base64 encoded PNG
            'width': int,
            'height': int,
            'page_count': int,
            'title': str,           # PDF title if available
            'error': Optional[str]
        }
    """
    file_path = params.get('file')
    zoom = params.get('zoom', 0.5)

    if not file_path:
        return {'success': False, 'error': 'No file provided'}

    try:
        with fitz.open(file_path) as doc:
            if doc.page_count == 0:
                return {'success': False, 'error': 'PDF has no pages'}

            # Render first page
            page = doc[0]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            img_bytes = pix.tobytes("png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            # Get metadata
            metadata = doc.metadata
            title = metadata.get('title', '') or file_path.split('/')[-1].split('\\')[-1]

            return {
                'success': True,
                'image': img_base64,
                'width': pix.width,
                'height': pix.height,
                'page_count': doc.page_count,
                'title': title
            }

    except Exception as e:
        logger.exception("Error generating preview")
        return {'success': False, 'error': str(e)}


def get_page_preview(params: dict) -> dict:
    """
    Generate a preview for a specific page in a PDF file.

    Args:
        params: {
            'file': str,           # PDF file path
            'page': int,           # Page number (1-indexed)
            'zoom': float          # Optional: zoom factor (default: 1.0)
        }

    Returns:
        {
            'success': bool,
            'image': str,           # Base64 encoded PNG
            'width': int,           # Image width in pixels (at zoom level)
            'height': int,          # Image height in pixels (at zoom level)
            'page_width': float,    # Original page width in points
            'page_height': float,   # Original page height in points
            'error': Optional[str]
        }
    """
    file_path = params.get('file')
    page_num = params.get('page', 1) - 1  # Convert to 0-indexed
    zoom = params.get('zoom', 1.0)

    if not file_path:
        return {'success': False, 'error': 'No file provided'}

    try:
        with fitz.open(file_path) as doc:
            if doc.page_count == 0:
                return {'success': False, 'error': 'PDF has no pages'}

            if page_num < 0 or page_num >= doc.page_count:
                return {'success': False, 'error': f'Invalid page number: {page_num + 1}'}

            # Render specified page
            page = doc[page_num]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)

            img_bytes = pix.tobytes("png")
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            return {
                'success': True,
                'image': img_base64,
                'width': pix.width,
                'height': pix.height,
                'page_width': page.rect.width,
                'page_height': page.rect.height
            }

    except Exception as e:
        logger.exception("Error generating page preview")
        return {'success': False, 'error': str(e)}


def register(server):
    """Register thumbnail methods with the server"""
    server.register_method('pdf.get_thumbnails', get_thumbnails)
    server.register_method('pdf.get_file_preview', get_file_preview)
    server.register_method('pdf.get_page_preview', get_page_preview)
    logger.info("PDF thumbnail handler registered")
