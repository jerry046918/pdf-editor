"""PDF Split Handler"""

import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


def split_pdf(params: dict) -> dict:
    """
    Split a PDF file into multiple files.
    
    Args:
        params: {
            'file': str,          # Input PDF path
            'output_dir': str,    # Output directory
            'mode': str,          # 'range' | 'fixed' | 'extract' | 'bookmark'
            'options': {
                'ranges': Optional[list[tuple[int,int]]],  # For 'range' mode
                'pages_per_file': Optional[int],           # For 'fixed' mode
                'pages': Optional[list[int]],              # For 'extract' mode
                'prefix': Optional[str]                    # Output filename prefix
            }
        }
    
    Returns:
        {'success': bool, 'files': list[str], 'error': Optional[str]}
    """
    file_path = params.get('file')
    output_dir = params.get('output_dir')
    mode = params.get('mode', 'range')
    options = params.get('options', {})
    
    if not file_path:
        return {'success': False, 'error': 'No input file provided'}
    
    if not output_dir:
        return {'success': False, 'error': 'No output directory provided'}
    
    try:
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        with fitz.open(file_path) as src:
            total_pages = src.page_count
            prefix = options.get('prefix', 'split')
            output_files = []

            if mode == 'range':
                # Split by page ranges
                ranges = options.get('ranges', [])
                for i, (start, end) in enumerate(ranges):
                    output_path = str(Path(output_dir) / f"{prefix}_{i+1}.pdf")
                    with fitz.open() as result:
                        result.insert_pdf(src, from_page=start-1, to_page=end-1)
                        result.save(output_path)
                    output_files.append(output_path)
                    logger.info(f"Created: {output_path} (pages {start}-{end})")

            elif mode == 'fixed':
                # Split by fixed number of pages per file
                pages_per_file = options.get('pages_per_file', 1)
                # Validate pages_per_file
                if pages_per_file < 1:
                    return {'success': False, 'error': 'pages_per_file must be at least 1'}
                file_count = 0
                for start in range(0, total_pages, pages_per_file):
                    end = min(start + pages_per_file, total_pages)
                    output_path = str(Path(output_dir) / f"{prefix}_{file_count+1}.pdf")
                    with fitz.open() as result:
                        result.insert_pdf(src, from_page=start, to_page=end-1)
                        result.save(output_path)
                    output_files.append(output_path)
                    file_count += 1
                    logger.info(f"Created: {output_path} (pages {start+1}-{end})")

            elif mode == 'extract':
                # Extract specific pages
                pages = options.get('pages', [])
                output_path = str(Path(output_dir) / f"{prefix}_extracted.pdf")
                with fitz.open() as result:
                    for page_num in pages:
                        if 1 <= page_num <= total_pages:
                            result.insert_pdf(src, from_page=page_num-1, to_page=page_num-1)
                    result.save(output_path)
                output_files.append(output_path)
                logger.info(f"Created: {output_path} (pages {pages})")

            elif mode == 'bookmark':
                # Split by bookmarks (if available)
                toc = src.get_toc()
                if not toc:
                    return {'success': False, 'error': 'No bookmarks found in PDF'}

                # TODO: Implement bookmark-based splitting
                return {'success': False, 'error': 'Bookmark splitting not yet implemented'}

            logger.info(f"Split complete: {len(output_files)} files created")

            return {
                'success': True,
                'files': output_files,
                'total_files': len(output_files)
            }

    except Exception as e:
        logger.exception("Error splitting PDF")
        return {'success': False, 'error': str(e)}


def register(server):
    """Register split methods with the server"""
    server.register_method('pdf.split', split_pdf)
    logger.info("PDF split handler registered")
