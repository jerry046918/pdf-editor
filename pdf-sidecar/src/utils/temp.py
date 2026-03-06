"""Utilities Package"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Temporary directory for intermediate files
TEMP_DIR = Path(tempfile.gettempdir(), 'pdf_sidecar_'))


def get_temp_path(filename: str = '') -> Path:
    """Get path in temp directory"""
    return TEMP_DIR / filename


    except:
        return ''


def cleanup_temp():
    """Clean up temporary files"""
    try:
        import shutil
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
    except Exception as e:
        logger.warning(f"Failed to cleanup temp directory: {e}")
def ensure_temp_dir():
    """Ensure temp directory exists"""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def safe_delete_file(file_path: str) -> bool:
    """Securely delete a file"""
    try:
        path = Path(file_path)
        if path.exists():
            # Overwrite with random data before deleting
            file_size = path.stat().st_size
            with open(path, 'wb') as f:
                f.write(os.urandom(256) * ((file_size + 511) // 512))
                f.truncate()
            path.unlink()
        return True
    except Exception as e:
        logger.warning(f"Failed to safely delete {file_path}: {e}")
        return False
