"""Batch PDF Split Handler"""

import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def batch_split(params: dict) -> dict:
    """
    Split multiple PDF files with the same settings.
    
    Args:
        params: {
            'files': List[str],        # List of input PDF paths
            'output_dir': str,         # Output directory
            'mode': str,               # 'range' | 'fixed' | 'extract'
            'options': {
                'ranges': Optional[list[tuple[int,int]]],  # For 'range' mode
                'pages_per_file': Optional[int],           # For 'fixed' mode
                'pages': Optional[list[int]],              # For 'extract' mode
                'prefix': Optional[str]                    # Output filename prefix (ignored, uses source filename)
            }
        }
    
    Returns:
        {
            'success': bool,
            'results': list[dict],  # Per-file results
            'total_files': int,
            'success_count': int,
            'failed_count': int,
            'error': Optional[str]
        }
    """
    files = params.get('files', [])
    output_dir = params.get('output_dir')
    mode = params.get('mode', 'range')
    options = params.get('options', {})
    
    if not files:
        return {'success': False, 'error': 'No input files provided', 'results': [], 
                'total_files': 0, 'success_count': 0, 'failed_count': 0}
    
    if not output_dir:
        return {'success': False, 'error': 'No output directory provided', 'results': [], 
                'total_files': len(files), 'success_count': 0, 'failed_count': len(files)}
    
    # Ensure output directory exists
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return {'success': False, 'error': f'Failed to create output directory: {e}', 
                'results': [], 'total_files': len(files), 'success_count': 0, 'failed_count': len(files)}
    
    results = []
    success_count = 0
    failed_count = 0
    
    for file_path in files:
        result = _split_single_file(file_path, output_dir, mode, options)
        results.append(result)
        if result['success']:
            success_count += 1
        else:
            failed_count += 1
    
    logger.info(f"Batch split complete: {success_count} succeeded, {failed_count} failed")
    
    return {
        'success': True,
        'results': results,
        'total_files': len(files),
        'success_count': success_count,
        'failed_count': failed_count
    }


def _split_single_file(file_path: str, output_dir: str, mode: str, options: dict) -> dict:
    """
    Split a single PDF file. Returns result dict for this file.
    """
    try:
        # Generate prefix from source filename
        source_name = Path(file_path).stem
        prefix = f"{source_name}_split"

        with fitz.open(file_path) as src:
            total_pages = src.page_count
            output_files = []

            if mode == 'range':
                ranges = options.get('ranges', [])
                for i, (start, end) in enumerate(ranges):
                    # Validate range
                    if end > total_pages:
                        return {
                            'file': file_path,
                            'success': False,
                            'error': f'Range end ({end}) exceeds file page count ({total_pages})'
                        }

                    output_path = str(Path(output_dir) / f"{prefix}_{i+1}.pdf")
                    with fitz.open() as result:
                        result.insert_pdf(src, from_page=start-1, to_page=end-1)
                        result.save(output_path)
                    output_files.append(output_path)
                    logger.info(f"Created: {output_path} (pages {start}-{end})")

            elif mode == 'fixed':
                pages_per_file = options.get('pages_per_file', 1)
                # Validate pages_per_file
                if pages_per_file < 1:
                    return {
                        'file': file_path,
                        'success': False,
                        'error': 'pages_per_file must be at least 1'
                    }
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
                pages = options.get('pages', [])
                if not pages:
                    return {
                        'file': file_path,
                        'success': False,
                        'error': 'No pages specified for extract mode'
                    }

                # Validate all pages
                invalid_pages = [p for p in pages if p > total_pages]
                if invalid_pages:
                    return {
                        'file': file_path,
                        'success': False,
                        'error': f'Pages {invalid_pages} exceed file page count ({total_pages})'
                    }

                output_path = str(Path(output_dir) / f"{prefix}_extracted.pdf")
                with fitz.open() as result:
                    for page_num in pages:
                        result.insert_pdf(src, from_page=page_num-1, to_page=page_num-1)
                    result.save(output_path)
                output_files.append(output_path)
                logger.info(f"Created: {output_path} (pages {pages})")

            else:
                return {
                    'file': file_path,
                    'success': False,
                    'error': f'Unknown split mode: {mode}'
                }

            return {
                'file': file_path,
                'success': True,
                'output_files': output_files
            }

    except Exception as e:
        logger.exception(f"Error splitting {file_path}")
        return {
            'file': file_path,
            'success': False,
            'error': str(e)
        }


def register(server):
    """Register batch_split methods with the server"""
    server.register_method('pdf.batch_split', batch_split)
    logger.info("PDF batch split handler registered")
