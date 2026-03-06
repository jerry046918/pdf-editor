"""Image to PDF Conversion Handler"""

import fitz  # PyMuPDF
from PIL import Image
import logging
from pathlib import Path
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)


def convert_images_to_pdf(params: dict) -> dict:
    """
    Convert images to a PDF file.
    
    Args:
        params: {
            'images': list[str],   # Image file paths
            'output': str,         # Output PDF path
            'options': {
                'page_size': str | list[int],  # 'A4' | 'Letter' | [width, height]
                'orientation': str,            # 'auto' | 'portrait' | 'landscape'
                'margin': int,                 # Margin in points
                'quality': int,                # Image quality 1-100
                'fit': str                     # 'contain' | 'cover' | 'stretch'
            }
        }
    
    Returns:
        {'success': bool, 'page_count': int, 'file_size': int, 'error': Optional[str]}
    """
    images = params.get('images', [])
    output_path = params.get('output')
    options = params.get('options', {})
    
    if not images:
        return {'success': False, 'error': 'No images provided'}
    
    if not output_path:
        return {'success': False, 'error': 'No output path provided'}
    
    try:
        # Page size presets (in points, 1 point = 1/72 inch)
        page_sizes = {
            'A4': (595.28, 841.89),
            'Letter': (612, 792),
            'Legal': (612, 1008)
        }
        
        # Get page dimensions
        page_size = options.get('page_size', 'A4')
        if isinstance(page_size, str):
            width, height = page_sizes.get(page_size, page_sizes['A4'])
        else:
            width, height = page_size
        
        # Handle orientation
        orientation = options.get('orientation', 'auto')
        margin = options.get('margin', 20)
        quality = options.get('quality', 85)
        fit_mode = options.get('fit', 'contain')
        
        # Create PDF
        result = fitz.open()
        
        for i, image_path in enumerate(images):
            logger.info(f"Processing image {i+1}/{len(images)}: {image_path}")
            
            # Load image
            img = Image.open(image_path)
            
            # Auto-rotate based on EXIF
            if hasattr(img, '_getexif'):
                try:
                    from PIL import ImageOps
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    pass
            
            # Determine page orientation
            img_width, img_height = img.size
            if orientation == 'auto':
                if img_width > img_height:
                    page_width, page_height = height, width  # Landscape
                else:
                    page_width, page_height = width, height  # Portrait
            elif orientation == 'landscape':
                page_width, page_height = height, width
            else:
                page_width, page_height = width, height
            
            # Create page
            page = result.new_page(width=page_width, height=page_height)
            
            # Calculate image placement
            content_width = page_width - 2 * margin
            content_height = page_height - 2 * margin
            
            # Save image to bytes for PyMuPDF
            img_bytes_path = str(Path(image_path))
            
            # Insert image
            if fit_mode == 'contain':
                # Fit within bounds while maintaining aspect ratio
                page.insert_image(
                    fitz.Rect(margin, margin, page_width - margin, page_height - margin),
                    filename=img_bytes_path,
                    keep_proportion=True
                )
            elif fit_mode == 'cover':
                # Fill bounds, may crop
                page.insert_image(
                    fitz.Rect(margin, margin, page_width - margin, page_height - margin),
                    filename=img_bytes_path,
                    keep_proportion=False
                )
            else:  # stretch
                page.insert_image(
                    fitz.Rect(margin, margin, page_width - margin, page_height - margin),
                    filename=img_bytes_path
                )
        
        # Save result
        result.save(output_path, garbage=4, deflate=True)
        file_size = Path(output_path).stat().st_size
        
        logger.info(f"Conversion complete: {len(result)} pages, {file_size} bytes")
        
        return {
            'success': True,
            'page_count': len(result),
            'file_size': file_size
        }
        
    except Exception as e:
        logger.exception("Error converting images to PDF")
        return {'success': False, 'error': str(e)}


def register(server):
    """Register convert methods with the server"""
    server.register_method('pdf.convert_images', convert_images_to_pdf)
    logger.info("Image to PDF convert handler registered")
