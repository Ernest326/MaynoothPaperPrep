"""
Maynooth Paper Prep UI Module - Main Window Implementation
=========================================================

This file implements the main application window for the Maynooth Paper Prep application.
It provides a complete PySide6-based user interface with:
- User authentication form
- Module selection
- Output directory selection
- AI processing options
- Themeable interface (light/dark modes)
- Multithreaded background operations

The UI is designed to be responsive and user-friendly, preventing any freezing 
during long-running operations by offloading work to background threads.
"""

# Standard library imports
import sys
import re
import threading
from pathlib import Path

# PySide6 imports for UI components
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QFileDialog,
    QGroupBox, QGridLayout, QMessageBox, QFrame, QSizePolicy,
    QSpacerItem, QStatusBar
)
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor
from PySide6.QtCore import Qt, Signal, Slot, QThread

import scraper
from .styles import theme

class ScraperWorker(QThread):
    """
    Worker thread to run the scraper without blocking the UI.
    
    This class extends QThread to perform paper scraping operations in a background
    thread, keeping the UI responsive during potentially long-running operations.
    It communicates with the main thread using Qt's signal-slot mechanism.
    
    Signals:
        finished(bool, str): Emitted when scraping completes, with success status and message.
    """
    
    # Signal that will be emitted when the scraping is complete
    # - bool: Whether the scraping was successful
    # - str: Success message or error message
    finished = Signal(bool, str)
    
    def __init__(self, username, password, module_code, output_folder):
        """
        Initialize the worker thread with the necessary scraping parameters.
        
        Args:
            username (str): The student ID for Maynooth authentication
            password (str): The password for Maynooth authentication
            module_code (str): The module code to scrape papers for
            output_folder (str): The directory where scraped papers will be saved
        """
        # Initialize the parent QThread
        super().__init__()
        self.username = username
        self.password = password
        self.module_code = module_code
        self.output_folder = output_folder
        self.scraper = scraper.Scraper()
        
    def run(self):
        """
        Execute the scraping operation in the background thread.
        
        This method is automatically called when the thread's start() method is called.
        It runs the scraper with the provided authentication and module information,
        then emits the finished signal with the result.
        """
        # Run the scraper and get the result
        # The scraper.start method returns True on success or an error message on failure
        result = self.scraper.start(
            self.username,
            self.password,
            self.module_code.upper(),
            self.output_folder
        )
        
        # Signal the result back to the main thread
        if result is True:
            # Success case: emit True with a success message
            self.finished.emit(True, "Success")
        else:
            # Error case: emit False with the error message
            self.finished.emit(False, str(result))


class MainWindow(QMainWindow):
    """
    Main application window for the Maynooth Paper Prep application.
    
    This class provides the complete user interface for the application,
    including all form inputs, buttons, and status information. It handles
    user interactions, validates inputs, and manages the background scraping
    process through the ScraperWorker thread.
    """
    
    def __init__(self):
        """
        Initialize the main window with default settings and UI setup.
        
        This constructor:
        1. Calls the parent QMainWindow constructor
        2. Sets up window properties (title, size, etc.)
        3. Initializes application variables
        4. Sets up the user interface
        5. Applies the current theme
        """
        # Initialize the parent QMainWindow
        super().__init__()
        
        # Window settings
        self.setWindowTitle("Maynooth Paper Scraper")
        self.setGeometry(100, 100, 600, 400)
        
        # Application variables
        self.output_folder = "./papers"  # Default output folder
        
        # Set up the UI components
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        """
        Set up the user interface components and layout.
        
        This method:
        1. Creates the main widget and layout structure
        2. Sets up the header section with title and theme toggle
        3. Creates form sections for login, paper info, and AI settings
        4. Adds the start button and status bar
        5. Connects signals to slots for user interactions
        
        The UI uses a combination of layout managers (VBox, HBox, Grid) to
        organize components in a user-friendly manner.
        """
        # ======================================================================
        # Main widget and layout
        # ======================================================================
        # Create a central widget to hold all UI components
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create the main vertical layout for the central widget
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # ======================================================================
        # Header section with title and theme toggle
        # ======================================================================
        # Create a horizontal layout for the header section
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)  # Margins (left, top, right, bottom)
        
        # Create the title label with custom styling
        title_label = QLabel("Maynooth Paper Scraper")
        title_label.setObjectName("titleLabel")  # Set an object name for styling in CSS
        title_label.setFont(QFont("Arial", 16, QFont.Bold))  # Set font (family, size, weight)
        
        # Create the theme toggle button
        self.theme_button = QPushButton("Toggle Theme")  
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setToolTip("Toggle Dark/Light Theme")  # Set tooltip text
        # Connect the button's clicked signal to our toggle_theme method
        self.theme_button.clicked.connect(self.toggle_theme)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.theme_button)
        
        main_layout.addLayout(header_layout)
        
        # ======================================================================
        # Login Information Section
        # ======================================================================
        # Create a group box for the login section
        login_group = QGroupBox("Login Information")
        login_layout = QGridLayout()
        login_group.setLayout(login_layout)
        
        # Username
        username_label = QLabel("Username:")
        username_label.setObjectName("fieldLabel")  # CSS styling identifier
        self.username_input = QLineEdit()  # Create text input field
        self.username_input.setPlaceholderText("Student ID (e.g. 12345678)")  # Set placeholder text
        login_layout.addWidget(username_label, 0, 0)  # Add to layout at row 0, column 0
        login_layout.addWidget(self.username_input, 0, 1)  # Add to layout at row 0, column 1
        
        # Password
        password_label = QLabel("Password:")
        password_label.setObjectName("fieldLabel")  # CSS styling identifier
        self.password_input = QLineEdit()  # Create text input field
        self.password_input.setEchoMode(QLineEdit.Password)  # Mask characters for password
        self.password_input.setPlaceholderText("Your Maynooth account password")  # Set placeholder
        login_layout.addWidget(password_label, 1, 0)  # Add to layout at row 1, column 0
        login_layout.addWidget(self.password_input, 1, 1)  # Add to layout at row 1, column 1
        
        # Add the login group to the main layout
        main_layout.addWidget(login_group)
        
        # ======================================================================
        # Paper Information Section
        # ======================================================================
        # Create a group box for the paper information section
        paper_group = QGroupBox("Paper Information")
        paper_layout = QGridLayout()
        paper_group.setLayout(paper_layout)
        
        # Module Code
        module_label = QLabel("Module Code:")
        module_label.setObjectName("fieldLabel")  # CSS styling identifier
        self.module_input = QLineEdit()  # Create text input field
        self.module_input.setPlaceholderText("E.g. CS101")  # Set placeholder text
        paper_layout.addWidget(module_label, 0, 0)  # Add to layout at row 0, column 0
        paper_layout.addWidget(self.module_input, 0, 1)  # Add to layout at row 0, column 1
        
        # Output Directory field with browse button
        output_label = QLabel("Output Directory:")
        output_label.setObjectName("fieldLabel")  # CSS styling identifier
        
        # Create a horizontal layout for the directory field and browse button
        output_layout = QHBoxLayout()
        self.output_display = QLineEdit(self.output_folder)
        self.output_display.setReadOnly(True)  # Make it read-only as it's updated by the dialog
        
        # Create a browse button to open the directory selection dialog
        output_btn = QPushButton("Browse...")
        output_btn.setObjectName("browseButton")
        output_btn.clicked.connect(self.select_output_folder)
        
        # Add the components to the horizontal layout
        output_layout.addWidget(self.output_display)
        output_layout.addWidget(output_btn)
        
        # Add the label and layout to the paper section's grid layout
        paper_layout.addWidget(output_label, 1, 0)  # Add to layout at row 1, column 0
        paper_layout.addLayout(output_layout, 1, 1)  # Add to layout at row 1, column 1
        
        # Add the paper group to the main layout
        main_layout.addWidget(paper_group)
        
        # ======================================================================
        # AI Settings Section
        # ======================================================================
        # Create a group box for the AI settings
        ai_group = QGroupBox("AI Settings (Note generation currently unavailable)")
        ai_layout = QGridLayout()
        ai_group.setLayout(ai_layout)
        
        # API Key field
        api_label = QLabel("GPT API Key:")
        api_label.setObjectName("fieldLabel")  # CSS styling identifier
        self.api_input = QLineEdit()  # Create text input field
        self.api_input.setPlaceholderText("Enter your OpenAI API key")  # Set placeholder text
        ai_layout.addWidget(api_label, 0, 0)  # Add to layout at row 0, column 0
        ai_layout.addWidget(self.api_input, 0, 1, 1, 4)  # Add to layout at row 0, column 1, spanning 4 columns
        
        # Options
        options_label = QLabel("Options:")
        options_label.setObjectName("fieldLabel")  # CSS styling identifier
        ai_layout.addWidget(options_label, 1, 0)  # Add to layout at row 1, column 0
        
        # Checkboxes
        self.study_plan_cb = QCheckBox("Create Study Plan")
        self.questions_cb = QCheckBox("Create Sample Questions")
        self.flashcards_cb = QCheckBox("Create Flashcards")
        self.lolcat_cb = QCheckBox("lolcat")  # For fun, generates output in lolcat style
        
        # Add the checkboxes to the layout
        ai_layout.addWidget(self.study_plan_cb, 1, 1)  # Row 1, Column 1
        ai_layout.addWidget(self.questions_cb, 1, 2)   # Row 1, Column 2
        ai_layout.addWidget(self.flashcards_cb, 1, 3)  # Row 1, Column 3
        ai_layout.addWidget(self.lolcat_cb, 1, 4)      # Row 1, Column 4
        
        # Add the AI settings group to the main layout
        main_layout.addWidget(ai_group)
        
        # ======================================================================
        # Start Button Section
        # ======================================================================
        # Create a horizontal layout for centering the start button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")  # CSS styling identifier
        # Connect the button's clicked signal to our start_scraper method
        self.start_button.clicked.connect(self.start_scraper)
        
        # Add the button to the layout with stretches for centering
        button_layout.addWidget(self.start_button)
        button_layout.addStretch()  # Add flexible space after the button
        
        main_layout.addLayout(button_layout)
        
        # Add stretch to push everything to the top
        # This ensures the UI components are aligned at the top of the window
        # if the window is resized larger than needed
        main_layout.addStretch()
        
        # ======================================================================
        # Status Bar
        # ======================================================================
        # Create and set up the status bar at the bottom of the window
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def apply_theme(self):
        """
        Apply the current theme stylesheet to the application.
        
        This method retrieves the current theme's stylesheet from the theme
        manager and applies it to the main window, affecting all child widgets.
        The theme system supports both light and dark modes.
        """
        # Get the current theme's stylesheet from the theme manager
        # and apply it to the entire window
        self.setStyleSheet(theme.get_stylesheet())
        
    def toggle_theme(self):
        """
        Toggle between light and dark themes.
        
        This method:
        1. Toggles the theme in the theme manager
        2. Applies the new theme
        3. Updates the status bar with information about the current theme
        """
        # Toggle the theme in the theme manager (light->dark or dark->light)
        theme.toggle_theme()
        self.apply_theme()
        
        # Update the status bar with information about the current theme
        current_theme = "Dark" if theme.current_theme == "dark" else "Light"
        self.status_bar.showMessage(f"{current_theme} theme applied")
    
    def select_output_folder(self):
        """
        Open a file dialog to select the output folder for scraped papers.
        
        This method:
        1. Opens a directory selection dialog
        2. If a directory is selected, updates the output_folder variable
        3. Updates the displayed path in the UI
        
        The selected folder will be used as the destination for downloaded papers.
        """
        # Open a directory selection dialog
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            str(Path(self.output_folder).absolute())
        )
        
        # If a folder was selected (user didn't cancel the dialog)
        if folder_path:
                        self.output_folder = folder_path
                        self.output_display.setText(folder_path)
    
    def start_scraper(self):
        """
        Validate user inputs and start the scraping process.
        
        This method:
        1. Validates all required input fields
        2. Shows error messages if validation fails
        3. Disables the start button to prevent multiple scraping operations
        4. Creates and starts a ScraperWorker thread to handle the scraping
        5. Updates the UI to show that scraping is in progress
        
        The actual scraping is performed in a background thread to keep
        the UI responsive during the potentially long-running operation.
        """
        # ======================================================================
        # Input Validation
        # ======================================================================
        
        # Validate username (must be 8 digits for Maynooth student ID)
        if not re.search(r"[0-9]{8}", self.username_input.text()):
            # Show error message if validation fails
            QMessageBox.critical(
                self,
                "Error",
                "Invalid username format. Use your student ID (e.g., 12345678)"
            )
            return
            
        if not self.password_input.text():
            # Show error message if validation fails
            QMessageBox.critical(self, "Error", "Password cannot be empty")
            return  # Stop processing if validation fails
            
        # Validate module code (cannot be empty)
        if not self.module_input.text():
            # Show error message if validation fails
            QMessageBox.critical(self, "Error", "Module code cannot be empty")
            return  # Stop processing if validation fails
            
        # Validate output folder (cannot be empty)
        if not self.output_folder:
            # Show error message if validation fails
            QMessageBox.critical(self, "Error", "Output folder cannot be empty")
            return  # Stop processing if validation fails
        
        # ======================================================================
        # Prepare UI for Scraping
        # ======================================================================
        
        # Disable the start button to prevent multiple scraping operations
        self.start_button.setEnabled(False)
        
        # Change button text to indicate that scraping is in progress
        self.start_button.setText("Scraping...")
        
        # Update status bar to show that scraping is in progress
        self.status_bar.showMessage("Scraping in progress...")
        
        # ======================================================================
        # Start Scraping in Background Thread
        # ======================================================================
        
        # Create a worker thread for the scraping operation
        self.worker = ScraperWorker(
            self.username_input.text(),     # Student ID for login
            self.password_input.text(),     # Password for login
            self.module_input.text(),       # Module code to scrape
            self.output_folder              # Where to save the papers
        )
        
        # Connect the worker's finished signal to our callback method
        self.worker.finished.connect(self.on_scraper_finished)
        
        # Start the worker thread
        # This will call the worker's run() method in a separate thread
        self.worker.start()
    
    def on_scraper_finished(self, success, message):
        """
        Handle the completion of the scraper thread.
        
        This method is called when the ScraperWorker thread emits its finished signal.
        It updates the UI based on whether the scraping was successful or not.
        
        Args:
            success (bool): Whether the scraping operation was successful
            message (str): Success message or error message
        """
        # ======================================================================
        # Restore UI State
        # ======================================================================
        
        # Re-enable the start button
        self.start_button.setEnabled(True)
        self.start_button.setText("Start")
        
        # ======================================================================
        # Handle Success or Failure
        # ======================================================================
        
        if success:
            # In case of success:
            
            # Log to console that we're generating notes (future feature)
            print("Generating Notes...")
            
            # Update status bar with success message
            self.status_bar.showMessage("Scraping completed successfully!")
            
            # Show success message dialog
            QMessageBox.information(self, "Success", "Scraping completed successfully!")
        else:
            # In case of failure:
            
            # Update status bar with error message
            self.status_bar.showMessage("Error: Scraping failed")
            
            # Show error message dialog with the specific error message
            QMessageBox.critical(self, "Error", message)


def run_app():
    """
    Initialize and run the application.
    
    This is the main entry point for starting the application. It:
    1. Creates a QApplication instance (required for all Qt applications)
    2. Creates the main window
    3. Shows the window
    4. Starts the Qt event loop
    
    The application will continue running until the user closes the window
    or calls sys.exit() from elsewhere in the code.
    """
    # Create a QApplication instance
    # QApplication manages the GUI application's control flow and main settings
    app = QApplication(sys.argv)  # Pass command line arguments to the application
    
    # Create the main window
    window = MainWindow()
    
    # Show the window
    window.show()
    
    # Start the application's event loop
    # This call will block until the application exits
    sys.exit(app.exec())