"""PDF Text Edit Handler"""

import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def edit_text(params: dict) -> dict:
    """
    Edit text in a PDF file.
    
    Args:
        params: {
            'file': str,          # Input PDF path
            'output': str,        # Output PDF path
            'operations': list[{  # List of operations
                'type': str,       # 'replace' | 'add' | 'delete'
                'page': int,       # Page number (1-indexed)
                'search': Optional[str],     # For 'replace'
                'replace': Optional[str],    # For 'replace'
                'text': Optional[str],       # For 'add'
                'position': Optional[list],  # [x, y] for 'add'
                'font': Optional[dict]       # Font settings
            }]
        }
    
    Returns:
        {'success': bool, 'operations_completed': int, 'error': Optional[str]}
    """
    file_path = params.get('file')
    output_path = params.get('output')
    operations = params.get('operations', [])
    
    if not file_path:
        return {'success': False, 'error': 'No input file provided'}
    
    if not output_path:
        return {'success': False, 'error': 'No output path provided'}
    
    if not operations:
        return {'success': False, 'error': 'No operations provided'}
    
    try:
        doc = fitz.open(file_path)
        completed = 0
        
        for op in operations:
            op_type = op.get('type')
            page_num = op.get('page', 1) - 1  # Convert to 0-indexed
            
            if page_num < 0 or page_num >= doc.page_count:
                logger.warning(f"Invalid page number: {page_num + 1}")
                continue
            
            page = doc[page_num]
            
            if op_type == 'replace':
                # Search and replace text
                search_text = op.get('search')
                replace_text = op.get('replace', '')
                
                if not search_text:
                    continue
                
                # Find text instances
                instances = page.search_for(search_text)
                
                for inst in reversed(instances):  # Reverse to avoid offset issues
                    # Redact old text
                    page.add_redact_annot(inst, fill=(1, 1, 1))
                    page.apply_redactions()
                    
                    # Insert new text at same position
                    font_settings = op.get('font', {})
                    fontname = font_settings.get('family', 'helv')
                    fontsize = font_settings.get('size', 11)
                    color = hex_to_rgb(font_settings.get('color', '#000000'))
                    
                    page.insert_text(
                        (inst.x0, inst.y1 - 2),
                        replace_text,
                        fontname=fontname,
                        fontsize=fontsize,
                        color=color
                    )
                
                completed += 1
                logger.info(f"Replaced '{search_text}' with '{replace_text}' on page {page_num + 1}")
                
            elif op_type == 'add':
                # Add new text
                text = op.get('text', '')
                position = op.get('position', [100, 100])
                
                font_settings = op.get('font', {})
                fontname = font_settings.get('family', 'helv')
                fontsize = font_settings.get('size', 11)
                color = hex_to_rgb(font_settings.get('color', '#000000'))
                
                page.insert_text(
                    (position[0], position[1]),
                    text,
                    fontname=fontname,
                    fontsize=fontsize,
                    color=color
                )
                
                completed += 1
                logger.info(f"Added text on page {page_num + 1}")
                
            elif op_type == 'delete':
                # Delete text (search and redact)
                search_text = op.get('search')
                
                if search_text:
                    instances = page.search_for(search_text)
                    for inst in instances:
                        page.add_redact_annot(inst, fill=(1, 1, 1))
                    page.apply_redactions()
                    completed += 1
                    logger.info(f"Deleted text '{search_text}' on page {page_num + 1}")
        
        # Save result
        doc.save(output_path)
        doc.close()
        
        logger.info(f"Edit complete: {completed} operations")
        
        return {
            'success': True,
            'operations_completed': completed
        }
        
    except Exception as e:
        logger.exception("Error editing PDF text")
        return {'success': False, 'error': str(e)}


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255 for i in (0, 2, 4))


def register(server):
    """Register edit methods with the server"""
    server.register_method('pdf.edit_text', edit_text)
    logger.info("PDF text edit handler registered")
