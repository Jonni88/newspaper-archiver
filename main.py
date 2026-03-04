#!/usr/bin/env python3
"""Main entry point for Newspaper Archiver application."""
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app import MainWindow


def main():
    """Main function."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("Архив газет Олёкминска")
    app.setApplicationVersion("1.0.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
