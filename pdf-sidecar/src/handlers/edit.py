"""PDF Text Edit Handler"""

import fitz  # PyMuPDF
import logging
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Font directories - prioritize bundled fonts, then system fonts
def get_font_directories() -> List[str]:
    """Get list of font directories to search, in priority order."""
    dirs = []

    # 1. Bundled fonts directory (set via environment variable)
    bundled_dir = os.environ.get('PDF_EDITOR_FONTS_DIR')
    if bundled_dir and os.path.isdir(bundled_dir):
        dirs.append(bundled_dir)

    # 2. Windows system fonts
    if os.name == 'nt':
        windows_fonts = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'Fonts')
        if os.path.isdir(windows_fonts):
            dirs.append(windows_fonts)

    return dirs

# Font file mapping - maps font name patterns to font files
# Format: 'pattern': ('bundled_font.ttf', ...)
BUNDLED_FONT_MAPPING = {
    # Hei/Black fonts -> bundled Noto Sans SC (黑体风格)
    'hei': ('NotoSansSC-Bold.ttf', 'NotoSansSC-Regular.ttf'),
    '黑': ('NotoSansSC-Bold.ttf', 'NotoSansSC-Regular.ttf'),
    'simhei': ('NotoSansSC-Bold.ttf',),
    '黑体': ('NotoSansSC-Bold.ttf',),
    'notosans': ('NotoSansSC-Regular.ttf', 'NotoSansSC-Bold.ttf'),

    # Song/Serif fonts -> bundled Noto Serif SC (宋体风格)
    'song': ('NotoSerifSC-Regular.ttf', 'NotoSerifSC-Bold.ttf'),
    '宋': ('NotoSerifSC-Regular.ttf', 'NotoSerifSC-Bold.ttf'),
    'simsun': ('NotoSerifSC-Regular.ttf',),
    '宋体': ('NotoSerifSC-Regular.ttf',),
    'notoserif': ('NotoSerifSC-Regular.ttf', 'NotoSerifSC-Bold.ttf'),
    'serif': ('NotoSerifSC-Regular.ttf',),

    # Fangsong -> use Song fallback
    'fangsong': ('NotoSerifSC-Regular.ttf',),
    '仿宋': ('NotoSerifSC-Regular.ttf',),

    # Kai fonts -> bundled TW-Kai (楷体风格)
    'kai': ('TW-Kai-98_1.ttf',),
    '楷': ('TW-Kai-98_1.ttf',),
    'simkai': ('TW-Kai-98_1.ttf',),
    '楷体': ('TW-Kai-98_1.ttf',),
    'stkaiti': ('TW-Kai-98_1.ttf',),
    'tw-kai': ('TW-Kai-98_1.ttf',),

    # Microsoft YaHei - use Noto Sans SC as substitute
    'microsoftyahei': ('NotoSansSC-Regular.ttf',),
    '微软雅黑': ('NotoSansSC-Regular.ttf',),
    'yahei': ('NotoSansSC-Regular.ttf',),

    # DengXian (等线) - use Noto Sans SC as substitute
    'dengxian': ('NotoSansSC-Regular.ttf',),
    '等线': ('NotoSansSC-Regular.ttf',),
}

# System font mapping (fallback when bundled fonts not available)
SYSTEM_FONT_MAPPING = {
    'hei': ('simhei.ttf', 'STXIHEI.TTF'),
    '黑': ('simhei.ttf', 'STXIHEI.TTF'),
    'simhei': ('simhei.ttf',),
    '黑体': ('simhei.ttf',),
    'kai': ('simkai.ttf', 'STKAITI.TTF'),  # 优先使用系统楷体
    '楷': ('simkai.ttf', 'STKAITI.TTF'),
    'simkai': ('simkai.ttf',),
    '楷体': ('simkai.ttf',),
    'stkaiti': ('STKAITI.TTF',),
    'microsoftyahei': ('msyh.ttc',),
    '微软雅黑': ('msyh.ttc',),
    'yahei': ('msyh.ttc',),
    'song': None,  # Use china-s
    '宋': None,
    'simsun': None,
    '宋体': None,
    'fangsong': None,
    '仿宋': None,
    'dengxian': None,
    '等线': None,
}

# Western font mapping to PyMuPDF built-in fonts
WESTERN_FONT_MAPPING = {
    'arial': 'helv',
    'helvetica': 'helv',
    'times': 'tiro',
    'courier': 'cour',
}


def find_font_file(font_files: Tuple[str, ...], font_dirs: List[str]) -> Optional[str]:
    """
    Search for a font file in the given directories.

    Args:
        font_files: Tuple of possible font filenames
        font_dirs: List of directories to search

    Returns:
        Full path to font file, or None if not found
    """
    for font_dir in font_dirs:
        for font_file in font_files:
            font_path = os.path.join(font_dir, font_file)
            if os.path.exists(font_path):
                return font_path
    return None


def get_font_file(original_font: str) -> Tuple[Optional[str], str]:
    """
    Get font file path and fontname for a given font name.
    Prioritizes bundled fonts, falls back to system fonts.

    Args:
        original_font: The original font name from the PDF

    Returns:
        Tuple of (font_file_path or None, fontname)
        - font_file_path: Path to .ttf/.ttc file, or None to use built-in font
        - fontname: The fontname to use (for built-in fonts or embedded font name)
    """
    if not original_font:
        return (None, 'china-s')

    font_dirs = get_font_directories()
    original_lower = original_font.lower().replace('-', '').replace('_', '').replace(' ', '')

    # First, try bundled fonts
    for key, font_files in BUNDLED_FONT_MAPPING.items():
        if font_files is None:
            continue
        if key in original_font or key in original_lower:
            font_path = find_font_file(font_files, font_dirs)
            if font_path:
                logger.debug(f"Matched font '{original_font}' to bundled: {font_path}")
                # Use filename without extension as fontname
                fontname = os.path.splitext(os.path.basename(font_path))[0]
                return (font_path, fontname)

    # Check Western fonts (use built-in)
    for key, builtin_name in WESTERN_FONT_MAPPING.items():
        if key in original_lower:
            return (None, builtin_name)

    # Fall back to system fonts
    for key, font_files in SYSTEM_FONT_MAPPING.items():
        if font_files is None:
            if key in original_font or key in original_lower:
                return (None, 'china-s')
            continue
        if key in original_font or key in original_lower:
            font_path = find_font_file(font_files, font_dirs)
            if font_path:
                logger.debug(f"Matched font '{original_font}' to system: {font_path}")
                fontname = os.path.splitext(os.path.basename(font_path))[0]
                return (font_path, fontname)

    # Check if this is a font that should use built-in china-s
    for key, font_files in SYSTEM_FONT_MAPPING.items():
        if font_files is None:
            if key in original_font or key in original_lower:
                return (None, 'china-s')

    # Default: use china-s for CJK fonts
    has_cjk_in_name = any('\u4e00' <= c <= '\u9fff' for c in original_font)
    if has_cjk_in_name:
        return (None, 'china-s')
    return (None, 'helv')


def get_matching_font(original_font: str, text: str) -> str:
    """
    Get a suitable fontname for inserting text (legacy function for backward compatibility).

    Args:
        original_font: The original font name from the PDF
        text: The text to be inserted

    Returns:
        fontname string
    """
    _, fontname = get_font_file(original_font)
    return fontname


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
        with fitz.open(file_path) as doc:
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
                    bbox = op.get('bbox')  # Optional bbox for precise positioning

                    if not search_text and not bbox:
                        continue

                    # If bbox is provided, use it directly for positioning
                    if bbox and len(bbox) == 4:
                        target_rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
                        instances = [target_rect]
                    else:
                        # Fall back to text search
                        instances = page.search_for(search_text)

                    for inst in reversed(instances):  # Reverse to avoid offset issues
                        # Try to detect original font from the text at this location
                        original_font = 'helv'
                        original_size = 11
                        original_color = (0, 0, 0)

                        # Get text info from the area around the match
                        try:
                            text_dict = page.get_text("dict", clip=fitz.Rect(
                                inst.x0 - 5, inst.y0 - 5, inst.x1 + 5, inst.y1 + 5
                            ))
                            for block in text_dict.get("blocks", []):
                                if block.get("type") != 0:
                                    continue
                                for line in block.get("lines", []):
                                    for span in line.get("spans", []):
                                        span_text = span.get("text", "")
                                        # Check if this span contains our search text (if we have one)
                                        if search_text and search_text.lower() in span_text.lower():
                                            original_font = span.get("font", "helv")
                                            original_size = span.get("size", 11)
                                            # Color is BGR integer, convert to RGB tuple
                                            color_int = span.get("color", 0)
                                            if isinstance(color_int, int):
                                                r = ((color_int >> 16) & 0xFF) / 255
                                                g = ((color_int >> 8) & 0xFF) / 255
                                                b = (color_int & 0xFF) / 255
                                                original_color = (r, g, b)
                                            break
                                        elif not search_text and span_text.strip():
                                            # If no search text but have bbox, use first span's font
                                            original_font = span.get("font", "helv")
                                            original_size = span.get("size", 11)
                                            color_int = span.get("color", 0)
                                            if isinstance(color_int, int):
                                                r = ((color_int >> 16) & 0xFF) / 255
                                                g = ((color_int >> 8) & 0xFF) / 255
                                                b = (color_int & 0xFF) / 255
                                                original_color = (r, g, b)
                        except Exception as e:
                            logger.debug(f"Could not detect original font: {e}")

                        # Use provided font settings or fall back to detected original
                        font_settings = op.get('font', {})
                        font_family = font_settings.get('family', original_font)
                        font_file, fontname = get_font_file(font_family)
                        fontsize = font_settings.get('size') or original_size
                        color_input = font_settings.get('color')
                        if color_input:
                            color = hex_to_rgb(color_input)
                        else:
                            color = original_color

                        # Redact old text with white fill
                        page.add_redact_annot(inst, fill=(1, 1, 1))

                        # Apply redactions before inserting new text
                        page.apply_redactions()

                        # Insert new text with matched font
                        try:
                            if font_file:
                                # Use external font file - must specify both fontfile and fontname
                                # fontname here is the name for the embedded font in the PDF
                                page.insert_text(
                                    (inst.x0, inst.y0 + fontsize * 0.8),
                                    replace_text,
                                    fontname=fontname,
                                    fontfile=font_file,
                                    fontsize=fontsize,
                                    color=color
                                )
                            else:
                                # Use built-in font
                                page.insert_text(
                                    (inst.x0, inst.y0 + fontsize * 0.8),
                                    replace_text,
                                    fontname=fontname,
                                    fontsize=fontsize,
                                    color=color
                                )
                        except Exception as e:
                            logger.warning(f"Failed to insert text with font {font_file or fontname}: {e}")
                            # Fallback to china-s for CJK, helv for others
                            has_cjk = any('\u4e00' <= c <= '\u9fff' for c in replace_text)
                            fallback_font = 'china-s' if has_cjk else 'helv'
                            page.insert_text(
                                (inst.x0, inst.y0 + fontsize * 0.8),
                                replace_text,
                                fontname=fallback_font,
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
                    fontsize = font_settings.get('size', 11)
                    color = hex_to_rgb(font_settings.get('color', '#000000'))

                    # Get font file and name
                    font_family = font_settings.get('family', 'helv')
                    font_file, fontname = get_font_file(font_family)

                    try:
                        if font_file:
                            # Use external font file - must specify both fontfile and fontname
                            page.insert_text(
                                (position[0], position[1]),
                                text,
                                fontname=fontname,
                                fontfile=font_file,
                                fontsize=fontsize,
                                color=color
                            )
                        else:
                            page.insert_text(
                                (position[0], position[1]),
                                text,
                                fontname=fontname,
                                fontsize=fontsize,
                                color=color
                            )
                    except Exception as e:
                        logger.warning(f"Failed to add text with font {font_file or fontname}: {e}")
                        # Fallback
                        has_cjk = any('\u4e00' <= c <= '\u9fff' for c in text)
                        fallback_font = 'china-s' if has_cjk else 'helv'
                        page.insert_text(
                            (position[0], position[1]),
                            text,
                            fontname=fallback_font,
                            fontsize=fontsize,
                            color=color
                        )

                    completed += 1
                    logger.info(f"Added text on page {page_num + 1}")

                elif op_type == 'delete':
                    # Delete text (search and redact)
                    search_text = op.get('search')
                    bbox = op.get('bbox')

                    if bbox and len(bbox) == 4:
                        # Use bbox directly if provided
                        target_rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
                        page.add_redact_annot(target_rect, fill=(1, 1, 1))
                        page.apply_redactions()
                        completed += 1
                        logger.info(f"Deleted text at bbox {bbox} on page {page_num + 1}")
                    elif search_text:
                        instances = page.search_for(search_text)
                        for inst in instances:
                            page.add_redact_annot(inst, fill=(1, 1, 1))
                        page.apply_redactions()
                        completed += 1
                        logger.info(f"Deleted text '{search_text}' on page {page_num + 1}")

            # Save result
            doc.save(output_path)

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


def get_text_blocks(params: dict) -> dict:
    """
    Extract text blocks from a specific page in a PDF.
    Uses strict paragraph merging: adjacent lines with same font and close spacing
    are merged into paragraphs.

    Args:
        params: {
            'file': str,     # Input PDF path
            'page': int      # Page number (1-indexed)
        }

    Returns:
        {
            'success': bool,
            'blocks': [{'id': str, 'text': str, 'bbox': [x0, y0, x1, y1], 'page': int, 'font': dict}],
            'page_width': int,
            'page_height': int,
            'error': Optional[str]
        }
    """
    file_path = params.get('file')
    page_num = params.get('page', 1) - 1  # Convert to 0-indexed

    if not file_path:
        return {'success': False, 'error': 'No input file provided'}

    try:
        with fitz.open(file_path) as doc:
            if page_num < 0 or page_num >= doc.page_count:
                return {'success': False, 'error': f'Invalid page number: {page_num + 1}'}

            page = doc[page_num]

            # Get detailed text information
            text_dict = page.get_text("dict")

            # Step 1: Extract all lines with their properties
            all_lines = []
            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:  # Skip image blocks
                    continue

                for line in block.get("lines", []):
                    line_bbox = line.get("bbox", (0, 0, 0, 0))
                    line_text = ""
                    line_font = None
                    line_size = None
                    line_color = '#000000'

                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        line_text += span_text

                        # Use first non-empty span for font info
                        if span_text.strip() and line_font is None:
                            line_font = span.get("font", "helv")
                            line_size = span.get("size", 11)
                            # Color is stored as integer (BGR format), convert to hex RGB
                            color_int = span.get("color", 0)
                            if isinstance(color_int, int):
                                r = (color_int >> 16) & 0xFF
                                g = (color_int >> 8) & 0xFF
                                b = color_int & 0xFF
                                line_color = f"#{r:02x}{g:02x}{b:02x}"

                    if line_text.strip():
                        all_lines.append({
                            'text': line_text,
                            'bbox': line_bbox,
                            'font': line_font or 'helv',
                            'size': round(line_size, 11) if line_size else 11,
                            'color': line_color
                        })

            if not all_lines:
                return {
                    'success': True,
                    'blocks': [],
                    'page_width': page.rect.width,
                    'page_height': page.rect.height
                }

            # Step 2: Sort lines by Y position (top to bottom), then by X position (left to right)
            all_lines.sort(key=lambda l: (l['bbox'][1], l['bbox'][0]))

            # Step 3: Merge lines into paragraphs based on strict criteria
            paragraphs = []
            current_para = None

            for line in all_lines:
                if current_para is None:
                    # Start first paragraph
                    current_para = {
                        'lines': [line],
                        'bbox': list(line['bbox']),
                        'font': line['font'],
                        'size': line['size'],
                        'color': line['color']
                    }
                else:
                    # Check if this line should be merged with current paragraph
                    should_merge = _should_merge_lines(current_para, line)

                    if should_merge:
                        # Merge into current paragraph
                        current_para['lines'].append(line)
                        # Expand bbox to include this line
                        curr_bbox = current_para['bbox']
                        line_bbox = line['bbox']
                        current_para['bbox'] = [
                            min(curr_bbox[0], line_bbox[0]),  # x0
                            min(curr_bbox[1], line_bbox[1]),  # y0
                            max(curr_bbox[2], line_bbox[2]),  # x1
                            max(curr_bbox[3], line_bbox[3])   # y1
                        ]
                    else:
                        # Save current paragraph and start new one
                        paragraphs.append(current_para)
                        current_para = {
                            'lines': [line],
                            'bbox': list(line['bbox']),
                            'font': line['font'],
                            'size': line['size'],
                            'color': line['color']
                        }

            # Don't forget the last paragraph
            if current_para:
                paragraphs.append(current_para)

            # Step 4: Build final blocks list
            blocks = []
            for idx, para in enumerate(paragraphs):
                # Join lines with space (for wrapped text) or newline
                # Use newline to preserve paragraph structure
                text = '\n'.join(line['text'] for line in para['lines'])

                blocks.append({
                    'id': f"block_{page_num}_{idx}",
                    'text': text,
                    'bbox': para['bbox'],
                    'page': page_num + 1,
                    'font': {
                        'family': para['font'],
                        'size': para['size'],
                        'color': para['color']
                    }
                })

            return {
                'success': True,
                'blocks': blocks,
                'page_width': page.rect.width,
                'page_height': page.rect.height
            }

    except Exception as e:
        logger.exception("Error extracting text blocks")
        return {'success': False, 'error': str(e)}


def _should_merge_lines(current_para: dict, next_line: dict) -> bool:
    """
    Determine if next_line should be merged into current paragraph.
    Uses strict criteria: same font, same size, close vertical spacing.

    Args:
        current_para: Current paragraph being built
        next_line: Candidate line to merge

    Returns:
        True if lines should be merged, False otherwise
    """
    # Get the last line in current paragraph
    last_line = current_para['lines'][-1]
    last_bbox = last_line['bbox']
    next_bbox = next_line['bbox']

    # Check 1: Font must match (case-insensitive)
    if last_line['font'].lower() != next_line['font'].lower():
        return False

    # Check 2: Font size must match (with small tolerance for rounding)
    if abs(last_line['size'] - next_line['size']) > 0.5:
        return False

    # Check 3: Vertical spacing must be reasonable
    # Calculate expected line spacing based on font size
    font_size = last_line['size']
    max_gap = font_size * 1.2  # Maximum gap threshold (1.2x font size)

    # Distance from bottom of last line to top of next line
    last_bottom = last_bbox[3]
    next_top = next_bbox[1]
    vertical_gap = next_top - last_bottom

    if vertical_gap > max_gap:
        return False

    # Check 4: Lines should overlap horizontally (same column)
    # Allow some tolerance for slight misalignment
    last_left = last_bbox[0]
    last_right = last_bbox[2]
    next_left = next_bbox[0]
    next_right = next_bbox[2]

    # Check if there's horizontal overlap
    has_horizontal_overlap = not (next_right < last_left - 10 or next_left > last_right + 10)

    return has_horizontal_overlap


def search_text(params: dict) -> dict:
    """
    Search for text across all pages in a PDF.

    Args:
        params: {
            'file': str,              # Input PDF path
            'search': str,            # Search text
            'case_sensitive': bool,   # Case sensitive search (default: False)
            'pages': Optional[list]   # Specific pages to search (1-indexed)
        }

    Returns:
        {
            'success': bool,
            'matches': [{'page': int, 'text': str, 'bbox': [x0, y0, x1, y1], 'context': str}],
            'total_matches': int,
            'error': Optional[str]
        }
    """
    file_path = params.get('file')
    search_text = params.get('search', '')
    case_sensitive = params.get('case_sensitive', False)
    pages_filter = params.get('pages')  # Optional page filter

    if not file_path:
        return {'success': False, 'error': 'No input file provided'}

    if not search_text:
        return {'success': False, 'error': 'No search text provided'}

    try:
        matches = []

        with fitz.open(file_path) as doc:
            # Determine which pages to search
            if pages_filter:
                pages_to_search = [p - 1 for p in pages_filter if 1 <= p <= doc.page_count]
            else:
                pages_to_search = range(doc.page_count)

            for page_idx in pages_to_search:
                page = doc[page_idx]

                # Search for text occurrences
                # PyMuPDF's search_for is case-sensitive by default
                if case_sensitive:
                    instances = page.search_for(search_text, quads=False)
                else:
                    # For case-insensitive search, we need a different approach
                    # Get all text spans and find matches manually
                    instances = []
                    text_dict = page.get_text("dict")
                    search_lower = search_text.lower()

                    for block in text_dict.get("blocks", []):
                        if block.get("type") != 0:
                            continue
                        for line in block.get("lines", []):
                            for span in line.get("spans", []):
                                span_text = span.get("text", "")
                                span_lower = span_text.lower()

                                # Find all occurrences in this span
                                start = 0
                                while True:
                                    pos = span_lower.find(search_lower, start)
                                    if pos == -1:
                                        break

                                    # Calculate approximate bbox for the matched text
                                    # This is an approximation based on character width
                                    span_bbox = span.get("bbox", (0, 0, 0, 0))
                                    span_width = span_bbox[2] - span_bbox[0]
                                    char_width = span_width / len(span_text) if span_text else 0

                                    match_x0 = span_bbox[0] + pos * char_width
                                    match_x1 = span_bbox[0] + (pos + len(search_text)) * char_width

                                    instances.append(fitz.Rect(match_x0, span_bbox[1], match_x1, span_bbox[3]))
                                    start = pos + 1

                for inst in instances:
                    # Get surrounding context
                    context_rect = fitz.Rect(
                        inst.x0 - 50,
                        inst.y0 - 10,
                        inst.x1 + 50,
                        inst.y1 + 10
                    )
                    # Clip to page bounds
                    context_rect = context_rect & page.rect

                    context_text = page.get_text("text", clip=context_rect).strip()
                    # Clean up context
                    context_text = " ".join(context_text.split())

                    matches.append({
                        'page': page_idx + 1,
                        'text': search_text,
                        'bbox': [inst.x0, inst.y0, inst.x1, inst.y1],
                        'context': context_text
                    })

        return {
            'success': True,
            'matches': matches,
            'total_matches': len(matches)
        }

    except Exception as e:
        logger.exception("Error searching text")
        return {'success': False, 'error': str(e)}


def register(server):
    """Register edit methods with the server"""
    server.register_method('pdf.edit_text', edit_text)
    server.register_method('pdf.get_text_blocks', get_text_blocks)
    server.register_method('pdf.search_text', search_text)
    logger.info("PDF text edit handler registered")
