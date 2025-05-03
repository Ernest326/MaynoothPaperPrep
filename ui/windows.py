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
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QGridLayout,
    QMessageBox,
    QFrame,
    QSizePolicy,
    QSpacerItem,
    QStatusBar,
    QTabWidget,
    QProgressBar,
    QListWidget,
    QComboBox,
    QDialog,
    QTextEdit,
    QFormLayout,
    QDialogButtonBox,
)
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor, QTextCursor
from PySide6.QtCore import Qt, Signal, Slot, QThread

import requests
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
        progress(int, int): Emitted to update progress, with current and total values.
    """

    # Signal that will be emitted when the scraping is complete
    # - bool: Whether the scraping was successful
    # - str: Success message or error message
    finished = Signal(bool, str)
    progress = Signal(int, int)  # current, total

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
        self.progress_callback = None

    def run(self):
        """
        Execute the scraping operation in the background thread.

        This method is automatically called when the thread's start() method is called.
        It runs the scraper with the provided authentication and module information,
        then emits the finished signal with the result.
        """

        # Define a progress callback to emit progress updates
        def progress_cb(current, total):
            self.progress.emit(current, total)

        # Assign the progress callback to the scraper
        self.scraper.progress_callback = progress_cb

        # Run the scraper and get the result
        # The scraper.start method returns True on success or an error message on failure
        result = self.scraper.start(
            self.username, self.password, self.module_code.upper(), self.output_folder
        )

        # Signal the result back to the main thread
        if result is True:
            # Success case: emit True with a success message
            self.finished.emit(True, "Success")
        else:
            # Error case: emit False with the error message
            self.finished.emit(False, str(result))


class OllamaWorker(QThread):
    """
    Worker thread to run Ollama AI generation without blocking the UI.
    Emits:
        finished(str): Emitted when generation completes, with the AI response.
        error(str): Emitted if an error occurs.
    """
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, prompt, model, settings):
        super().__init__()
        self.prompt = prompt
        self.model = model
        self.settings = settings

    def run(self):
        import requests
        model_name = self.model.replace("ollama:", "").strip()
        url = f"http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": self.prompt,
            "options": {
                "temperature": self.settings.get("temperature", 1.0),
                "num_predict": self.settings.get("max_tokens", 512),
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 200:
                data = resp.json()
                self.finished.emit(data.get("response", "(no response)"))
            else:
                self.error.emit(f"[Ollama error: {resp.status_code}]")
        except Exception as e:
            self.error.emit(f"[Ollama connection error: {e}]")


class ModelSettingsDialog(QDialog):
    """
    Dialog for configuring model parameters such as temperature and max tokens.
    Used for both OpenAI and local models (Ollama).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Settings")
        layout = QFormLayout(self)
        # Example settings
        self.temperature_input = QLineEdit("1.0")
        self.max_tokens_input = QLineEdit("512")
        layout.addRow("Temperature", self.temperature_input)
        layout.addRow("Max Tokens", self.max_tokens_input)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_settings(self):
        return {
            "temperature": float(self.temperature_input.text()),
            "max_tokens": int(self.max_tokens_input.text()),
        }


class MarkdownTextEdit(QTextEdit):
    """
    QTextEdit subclass that renders markdown as HTML for chat display.
    Used in the AI Generation tab for rich chat formatting.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAcceptRichText(True)

    def append_markdown(self, markdown_text):
        try:
            import markdown

            html = markdown.markdown(
                markdown_text, extensions=["fenced_code", "tables"]
            )
        except ImportError:
            html = markdown_text
        self.moveCursor(QTextCursor.End)
        self.insertHtml(html + "<br>")
        self.moveCursor(QTextCursor.End)


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
        Set up the main UI, including tabbed layout, all widgets, and signal connections.
        Tabs: Login Info, Downloads/Module Selection, AI Generation.
        """
        # ======================================================================
        # Main widget and layout
        # ======================================================================
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header section with title and theme toggle
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)
        title_label = QLabel("Maynooth Paper Scraper")
        title_label.setObjectName("titleLabel")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.theme_button = QPushButton("Toggle Theme")
        self.theme_button.setObjectName("themeButton")
        self.theme_button.setToolTip("Toggle Dark/Light Theme")
        self.theme_button.clicked.connect(self.toggle_theme)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.theme_button)
        main_layout.addLayout(header_layout)

        # ======================================================================
        # Tab Widget
        # ======================================================================
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # ------------------- Login Info Tab -------------------
        self.login_tab = QWidget()
        login_tab_layout = QVBoxLayout(self.login_tab)
        login_group = QGroupBox("Login Information")
        login_layout = QGridLayout()
        login_group.setLayout(login_layout)
        username_label = QLabel("Username:")
        username_label.setObjectName("fieldLabel")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Student ID (e.g. 12345678)")
        login_layout.addWidget(username_label, 0, 0)
        login_layout.addWidget(self.username_input, 0, 1)
        password_label = QLabel("Password:")
        password_label.setObjectName("fieldLabel")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Your Maynooth account password")
        login_layout.addWidget(password_label, 1, 0)
        login_layout.addWidget(self.password_input, 1, 1)
        login_tab_layout.addWidget(login_group)
        login_tab_layout.addStretch()
        self.tabs.addTab(self.login_tab, "Login Info")

        # ------------------- Downloads/Module Selection Tab -------------------
        self.downloads_tab = QWidget()
        downloads_tab_layout = QVBoxLayout(self.downloads_tab)
        # Module Listing group
        module_group = QGroupBox("Module Selection")
        module_layout = QVBoxLayout()
        module_group.setLayout(module_layout)
        self.module_checkboxes = []
        self.custom_modules = []
        # Placeholder: populate with template module codes
        template_modules = ["CS101", "CS102", "MA201", "PH301", "BI110"]
        for code in template_modules:
            cb = QCheckBox(code)
            self.module_checkboxes.append(cb)
            module_layout.addWidget(cb)
        # Custom module add/remove controls
        custom_layout = QHBoxLayout()
        self.custom_module_input = QLineEdit()
        self.custom_module_input.setPlaceholderText("Add custom module code...")
        self.add_custom_btn = QPushButton("Add")
        self.remove_custom_btn = QPushButton("Remove Selected")
        custom_layout.addWidget(self.custom_module_input)
        custom_layout.addWidget(self.add_custom_btn)
        custom_layout.addWidget(self.remove_custom_btn)
        module_layout.addLayout(custom_layout)
        self.add_custom_btn.clicked.connect(self.add_custom_module)
        self.remove_custom_btn.clicked.connect(self.remove_selected_custom_modules)
        downloads_tab_layout.addWidget(module_group)
        # Paper Info group
        paper_group = QGroupBox("Paper Information")
        paper_layout = QGridLayout()
        paper_group.setLayout(paper_layout)
        output_label = QLabel("Output Directory:")
        output_label.setObjectName("fieldLabel")
        output_layout = QHBoxLayout()
        self.output_display = QLineEdit(self.output_folder)
        self.output_display.setReadOnly(True)
        output_btn = QPushButton("Browse...")
        output_btn.setObjectName("browseButton")
        output_btn.clicked.connect(self.select_output_folder)
        output_layout.addWidget(self.output_display)
        output_layout.addWidget(output_btn)
        paper_layout.addWidget(output_label, 0, 0)
        paper_layout.addLayout(output_layout, 0, 1)
        downloads_tab_layout.addWidget(paper_group)
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        downloads_tab_layout.addWidget(self.progress_bar)
        # Start button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.start_button = QPushButton("Start")
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self.start_scraper)
        button_layout.addWidget(self.start_button)
        button_layout.addStretch()
        downloads_tab_layout.addLayout(button_layout)
        downloads_tab_layout.addStretch()
        self.tabs.addTab(self.downloads_tab, "Downloads / Module Selection")

        # ------------------- AI Generation Tab -------------------
        self.ai_tab = QWidget()
        ai_tab_layout = QVBoxLayout(self.ai_tab)
        # Markdown chat view
        self.message_list = MarkdownTextEdit()
        ai_tab_layout.addWidget(self.message_list)
        # Message input and send
        msg_input_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        msg_input_layout.addWidget(self.message_input)
        msg_input_layout.addWidget(self.send_button)
        ai_tab_layout.addLayout(msg_input_layout)
        # File add and model select
        file_model_layout = QHBoxLayout()
        self.add_file_button = QPushButton("Add File")
        self.add_file_button.clicked.connect(self.add_file)
        self.model_select = QComboBox()
        self.model_select.addItems(
            ["gpt-3.5-turbo", "gpt-4", "llama-2", "ollama:custom"]
        )  # Example models
        self.settings_button = QPushButton("Model Settings")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        file_model_layout.addWidget(self.add_file_button)
        file_model_layout.addWidget(QLabel("Model:"))
        file_model_layout.addWidget(self.model_select)
        file_model_layout.addWidget(self.settings_button)
        ai_tab_layout.addLayout(file_model_layout)
        self.tabs.addTab(self.ai_tab, "AI Generation")

        # ======================================================================
        # Status Bar
        # ======================================================================
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
            self, "Select Output Folder", str(Path(self.output_folder).absolute())
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
        # Collect all selected modules from the checklist
        selected_modules = [
            cb.text() for cb in self.module_checkboxes if cb.isChecked()
        ]
        selected_modules.extend(self.custom_modules)
        if not selected_modules:
            QMessageBox.critical(
                self, "Error", "Please select at least one module to download."
            )
            return
        if not self.password_input.text():
            QMessageBox.critical(self, "Error", "Password cannot be empty")
            return
        if not self.output_folder:
            QMessageBox.critical(self, "Error", "Output folder cannot be empty")
            return
        # Prepare UI for Scraping
        self.start_button.setEnabled(False)
        self.start_button.setText("Scraping...")
        self.status_bar.showMessage("Scraping in progress...")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        # Start scraping for each selected module, one after another
        self._modules_to_scrape = selected_modules
        self._current_scrape_index = 0
        self._scrape_next_module()

    def _scrape_next_module(self):
        """
        Internal: Start scraping the next module in the selected list.
        Called recursively until all modules are processed.
        """
        if self._current_scrape_index >= len(self._modules_to_scrape):
            self.on_scraper_finished(True, "All modules scraped.")
            return
        module_code = self._modules_to_scrape[self._current_scrape_index]
        self.worker = ScraperWorker(
            self.username_input.text(),
            self.password_input.text(),
            module_code,
            self.output_folder,
        )
        self.worker.finished.connect(self._on_module_scrape_finished)
        self.worker.progress.connect(self.on_download_progress)
        self.worker.start()
        self.status_bar.showMessage(
            f"Scraping {module_code} ({self._current_scrape_index+1}/{len(self._modules_to_scrape)})..."
        )

    def _on_module_scrape_finished(self, success, message):
        """
        Internal: Handle completion of a single module scrape.
        Continues to next module or finishes the process.
        """
        if not success:
            self.on_scraper_finished(False, message)
            return
        self._current_scrape_index += 1
        self._scrape_next_module()

    def on_scraper_finished(self, success, message):
        """
        Handle the completion of all scraping operations.
        Restores UI and shows result to the user.
        """
        self.start_button.setEnabled(True)
        self.start_button.setText("Start")
        self.progress_bar.setVisible(False)
        if success:
            self.status_bar.showMessage("Scraping completed successfully!")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_bar.showMessage("Error: Scraping failed")
            QMessageBox.critical(self, "Error", message)

    def on_download_progress(self, current, total):
        """
        Update the progress bar based on the current progress of the download.

        Args:
            current (int): The current progress value
            total (int): The total value for the progress
        """
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def send_message(self):
        """
        Send a message in the AI Generation tab.
        Renders user message, calls AI backend (Ollama or placeholder), and renders response as markdown.
        """
        text = self.message_input.text().strip()
        if text:
            self.message_list.append_markdown(f"**You:** {text}")
            self.message_input.clear()
            model = self.model_select.currentText()
            settings = getattr(
                self, "_model_settings", {"temperature": 1.0, "max_tokens": 512}
            )
            if model.startswith("ollama:") or model.lower().startswith("llama"):
                self.send_button.setEnabled(False)
                self.status_bar.showMessage("Generating AI response...")
                self.ollama_worker = OllamaWorker(text, model, settings)
                self.ollama_worker.finished.connect(self._on_ollama_finished)
                self.ollama_worker.error.connect(self._on_ollama_error)
                self.ollama_worker.start()
            else:
                response = "(response placeholder)"  # Replace with OpenAI call if needed
                self.message_list.append_markdown(f"**AI:** {response}")

    def _on_ollama_finished(self, response):
        self.message_list.append_markdown(f"**AI:** {response}")
        self.send_button.setEnabled(True)
        self.status_bar.showMessage("Ready")

    def _on_ollama_error(self, error_msg):
        self.message_list.append_markdown(f"**AI:** {error_msg}")
        self.send_button.setEnabled(True)
        self.status_bar.showMessage("Ready")

    def add_file(self):
        """
        Open a file dialog and add the selected file to the AI chat as a markdown entry.
        """
        file_path, _ = QFileDialog.getOpenFileName(self, "Add File")
        if file_path:
            self.message_list.append_markdown(f"[File added: `{file_path}`]")

    def open_settings_dialog(self):
        """
        Open the model settings dialog and store the selected parameters.
        """
        dlg = ModelSettingsDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self._model_settings = dlg.get_settings()

    def query_ollama(self, prompt, model, settings):
        """
        Query a locally running Ollama model with the given prompt and settings.
        Returns the model's response as a string.
        """
        # Assumes Ollama is running locally on default port
        model_name = model.replace("ollama:", "").strip()
        url = f"http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "options": {
                "temperature": settings.get("temperature", 1.0),
                "num_predict": settings.get("max_tokens", 512),
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 200:
                # Ollama streams responses, but for simplicity, just get the text
                data = resp.json()
                return data.get("response", "(no response)")
            else:
                return f"[Ollama error: {resp.status_code}]"
        except Exception as e:
            return f"[Ollama connection error: {e}]"

    def add_custom_module(self):
        """
        Add a custom module code to the module selection list.
        """
        custom_code = self.custom_module_input.text().strip()
        if custom_code and custom_code not in self.custom_modules:
            cb = QCheckBox(custom_code)
            self.module_checkboxes.append(cb)
            self.custom_modules.append(custom_code)
            self.tabs.widget(1).layout().itemAt(0).widget().layout().addWidget(cb)
            self.custom_module_input.clear()

    def remove_selected_custom_modules(self):
        """
        Remove selected custom module codes from the module selection list.
        """
        for cb in self.module_checkboxes[:]:
            if cb.isChecked() and cb.text() in self.custom_modules:
                self.module_checkboxes.remove(cb)
                self.custom_modules.remove(cb.text())
                cb.setParent(None)


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
