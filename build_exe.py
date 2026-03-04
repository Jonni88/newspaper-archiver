#!/usr/bin/env python3
"""Build script for creating Windows executable."""
import PyInstaller.__main__
import os
import sys


def build():
    """Build executable with PyInstaller."""
    args = [
        'main.py',
        '--name=Архив_газет_Олекминска',
        '--windowed',
        '--onefile',
        '--icon=NONE',
        '--add-data=README.md;.',
        '--hidden-import=paddleocr',
        '--hidden-import=PySide6',
        '--hidden-import=fitz',
        '--collect-all=paddleocr',
        '--collect-all=paddlepaddle',
        '--clean',
        '--noconfirm',
    ]
    
    print("Building executable...")
    PyInstaller.__main__.run(args)
    print("Done! Check dist/ folder.")


if __name__ == "__main__":
    build()
