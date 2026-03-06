# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for PDF Sidecar
"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['pyinstaller', '--version'],
    console=False,
    stdout_regex=r'PyInstaller (\d+\.\d+\.\d+)',
)

a = Path(Path(__file__).parent, 'src', '__main__.py')

a = Analysis(
    [sys.executable, str(a)],
    console=False,
    stdout_regex=r'.*',
)

block_cipher = None

# Data files
added_files = [
    ('src', 'src'),
]

# Hidden imports
hiddenimports = [
    'src.handlers',
    'src.handlers.merge',
    'src.handlers.split',
    'src.handlers.convert',
    'src.handlers.edit',
    'src.core',
    'src.core.pdf_ops',
    'src.utils',
    'src.utils.temp',
]

# Excludes
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
]

# Binary settings
exe = True
onedir = False
name = 'pdf-sidecar'
debug = False

# Strip settings
strip = True
upx = False
console = True

# Windows specific
uac_admin = False
