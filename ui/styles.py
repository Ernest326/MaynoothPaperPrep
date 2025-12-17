"""
Styling for the Maynooth Paper Prep application.
Provides light and dark themes with easy switching.
"""

import logging

logger = logging.getLogger(__name__)


class AppTheme:
    """Manages application themes and provides easy access to stylesheets"""

    def __init__(self):
        logger.debug("Initializing AppTheme instance")
        self.current_theme = "light"
        logger.info(f"Default theme set to: {self.current_theme}")

    def get_stylesheet(self):
        """Returns the current theme's stylesheet"""
        logger.debug(f"Getting stylesheet for theme: {self.current_theme}")
        if self.current_theme == "dark":
            logger.debug("Returning dark theme stylesheet")
            return self.dark_theme()
        else:
            logger.debug("Returning light theme stylesheet")
            return self.light_theme()

    def set_theme(self, theme_name):
        """Sets the current theme to either 'light' or 'dark'"""
        logger.info(f"Attempting to set theme to: {theme_name}")
        if theme_name in ["light", "dark"]:
            old_theme = self.current_theme
            self.current_theme = theme_name
            logger.info(f"Theme changed from '{old_theme}' to '{self.current_theme}'")
        else:
            logger.warning(f"Invalid theme name provided: {theme_name}. Must be 'light' or 'dark'")

    def toggle_theme(self):
        """Toggles between light and dark themes"""
        old_theme = self.current_theme
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        logger.info(f"Theme toggled from '{old_theme}' to '{self.current_theme}'")

    @staticmethod
    def light_theme():
        """Returns the light theme stylesheet"""
        return """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QWidget {
                color: #333333;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 6px;
                background: #fafafa;
                margin-top: 8px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                min-width: 120px;
                min-height: 28px;
                padding: 6px 16px;
                font-weight: bold;
                color: #3498db;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #222222;
                border-bottom: 2px solid #3498db;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1.5ex;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: #3498db;
            }
            QLineEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px;
                background-color: #fafafa;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: white;
            }
            QLabel#fieldLabel {
                font-weight: bold;
                color: #333333;
            }
            QPushButton {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 6px 12px;
                background-color: #f8f8f8;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #eeeeee;
                border-color: #bbbbbb;
            }
            QPushButton:pressed {
                background-color: #dddddd;
            }
            QPushButton#startButton {
                background-color: #3498db;
                color: white;
                border: 1px solid #2980b9;
                font-weight: bold;
                min-width: 120px;
                min-height: 30px;
            }
            QPushButton#startButton:hover {
                background-color: #2980b9;
            }
            QPushButton#startButton:disabled {
                background-color: #95a5a6;
                border-color: #7f8c8d;
            }
            QPushButton#browseButton {
                min-width: 80px;
            }
            QPushButton#themeButton {
                min-width: 30px;
                min-height: 30px;
                border-radius: 15px;
                padding: 3px;
            }
            QPushButton#settingsButton {
                min-width: 100px;
            }
            QCheckBox {
                spacing: 5px;
                font-size: 13px;
                padding: 2px 0px 2px 2px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #cccccc;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #3498db;
                background-color: #3498db;
            }
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background: #f0f0f0;
                height: 20px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
            QTextEdit, QListWidget {
                background: #fafafa;
                border: 1px solid #cccccc;
                border-radius: 5px;
                font-size: 13px;
                color: #222222;
            }
            QComboBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px 8px;
                background: #fafafa;
                min-width: 120px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #cccccc;
                background: #ffffff;
                selection-background-color: #3498db;
                selection-color: #ffffff;
            }
            QStatusBar {
                background-color: #f0f0f0;
                color: #333333;
                border-top: 1px solid #cccccc;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #cccccc;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """

    @staticmethod
    def dark_theme():
        """Returns the dark theme stylesheet"""
        return """
            QMainWindow {
                background-color: #2c3e50;
            }
            QWidget {
                color: #ecf0f1;
            }
            QTabWidget::pane {
                border: 1px solid #34495e;
                border-radius: 6px;
                background: #34495e;
                margin-top: 8px;
            }
            QTabBar::tab {
                background: #22303a;
                border: 1px solid #34495e;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                min-width: 120px;
                min-height: 28px;
                padding: 6px 16px;
                font-weight: bold;
                color: #3498db;
            }
            QTabBar::tab:selected {
                background: #2c3e50;
                color: #ffffff;
                border-bottom: 2px solid #3498db;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #34495e;
                border-radius: 5px;
                margin-top: 1.5ex;
                padding-top: 10px;
                background-color: #22303a;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                color: #3498db;
            }
            QLineEdit {
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 6px;
                background-color: #1a2530;
                color: #ecf0f1;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #1a2530;
            }
            QLabel#fieldLabel {
                font-weight: bold;
                color: #ecf0f1;
            }
            QPushButton {
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 6px 12px;
                background-color: #34495e;
                color: #ecf0f1;
            }
            QPushButton:hover {
                background-color: #2c3e50;
                border-color: #95a5a6;
            }
            QPushButton:pressed {
                background-color: #1a2530;
            }
            QPushButton#startButton {
                background-color: #2980b9;
                color: white;
                border: 1px solid #3498db;
                font-weight: bold;
                min-width: 120px;
                min-height: 30px;
            }
            QPushButton#startButton:hover {
                background-color: #3498db;
            }
            QPushButton#startButton:disabled {
                background-color: #7f8c8d;
                border-color: #95a5a6;
            }
            QPushButton#browseButton {
                min-width: 80px;
            }
            QPushButton#themeButton {
                min-width: 30px;
                min-height: 30px;
                border-radius: 15px;
                padding: 3px;
            }
            QPushButton#settingsButton {
                min-width: 100px;
            }
            QCheckBox {
                spacing: 5px;
                font-size: 13px;
                padding: 2px 0px 2px 2px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #7f8c8d;
                background-color: #2c3e50;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #3498db;
                background-color: #3498db;
            }
            QProgressBar {
                border: 1px solid #34495e;
                border-radius: 5px;
                background: #22303a;
                height: 20px;
                text-align: center;
                font-weight: bold;
                color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 5px;
            }
            QTextEdit, QListWidget {
                background: #22303a;
                border: 1px solid #34495e;
                border-radius: 5px;
                font-size: 13px;
                color: #ecf0f1;
            }
            QComboBox {
                border: 1px solid #34495e;
                border-radius: 4px;
                padding: 4px 8px;
                background: #22303a;
                min-width: 120px;
                color: #ecf0f1;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #34495e;
                background: #34495e;
                selection-background-color: #3498db;
                selection-color: #ffffff;
            }
            QDialog {
                background: #22303a;
                color: #ecf0f1;
            }
            QDialog QLineEdit {
                background: #1a2530;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
            }
            QDialog QLabel {
                color: #ecf0f1;
            }
            QDialog QPushButton {
                background: #34495e;
                color: #ecf0f1;
                border: 1px solid #7f8c8d;
            }
            QDialog QPushButton:hover {
                background: #2980b9;
                color: #fff;
            }
            QStatusBar {
                background-color: #1a2530;
                color: #ecf0f1;
                border-top: 1px solid #34495e;
            }
            QScrollBar:vertical {
                border: none;
                background: #2c3e50;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #34495e;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """


# Create a singleton instance for easy access
theme = AppTheme()

# Export the theme instance
__all__ = ["theme"]
