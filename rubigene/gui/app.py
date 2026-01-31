"""
Rubigene Application Entry Point

Main application class and entry point for Rubigene.
"""

import sys
import os
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from .main_window import MainWindow


class RubigeneApp:
    """
    Main application class for Rubigene.
    
    Handles application initialization, styling, and window management.
    """
    
    APP_NAME = "Rubigene"
    APP_VERSION = "1.0.0"
    ORG_NAME = "Rubigene"
    ORG_DOMAIN = "rubigene.app"
    
    def __init__(self, argv: Optional[list] = None):
        """
        Initialize the Rubigene application.
        
        Args:
            argv: Command line arguments. Uses sys.argv if None.
        """
        self.argv = argv or sys.argv
        self.app: Optional[QApplication] = None
        self.main_window: Optional[MainWindow] = None
    
    def _get_resource_path(self, relative_path: str) -> str:
        """Get absolute path to resource, works for dev and PyInstaller."""
        if getattr(sys, 'frozen', False):
            # Running in a bundle
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
            else:
                base_path = Path(os.path.dirname(sys.executable)).parent / 'Resources'
        else:
            # Running in development
            base_path = Path(__file__).parent.parent
        
        return str(base_path / relative_path)
    
    def _setup_application(self):
        """Set up Qt application properties."""
        self.app = QApplication(self.argv)
        
        # Set application metadata
        self.app.setApplicationName(self.APP_NAME)
        self.app.setApplicationVersion(self.APP_VERSION)
        self.app.setOrganizationName(self.ORG_NAME)
        self.app.setOrganizationDomain(self.ORG_DOMAIN)
        
        # High DPI support
        self.app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
        
        # Set application icon
        icon_path = self._get_resource_path("app/icon.icns")
        if os.path.exists(icon_path):
            self.app.setWindowIcon(QIcon(icon_path))
    
    def _load_stylesheet(self):
        """Load and apply the application stylesheet."""
        style_path = self._get_resource_path("gui/style.qss")
        
        if os.path.exists(style_path):
            with open(style_path, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                self.app.setStyleSheet(stylesheet)
    
    def _create_main_window(self):
        """Create and configure the main window."""
        self.main_window = MainWindow()
    
    def run(self) -> int:
        """
        Run the application.
        
        Returns:
            Exit code from Qt application.
        """
        self._setup_application()
        self._load_stylesheet()
        self._create_main_window()
        
        self.main_window.show()
        
        return self.app.exec()


def main():
    """Main entry point for the application."""
    app = RubigeneApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
