"""
WordSeeker - Main Application
A modern PySide6 application for creating and solving word search puzzles.
"""

import sys
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QComboBox, QTextEdit,
    QListWidget, QListWidgetItem, QGroupBox, QMessageBox, QFileDialog,
    QInputDialog, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QAction, QPalette, QIcon

# Import from our modules
from constants import *
from utils import (
    get_gemini_key, save_gemini_key, load_themes, save_themes,
    validate_words, ApiWorker
)
from puzzle_engine import generate_word_search
from widgets import PuzzleGrid
from export import export_grid_to_png, export_grid_to_pdf


class WordSearchApp(QMainWindow):
    """Main application window for Word Search Creator."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QIcon('icon.png'))
        self.setGeometry(100, 100, 1200, 850)
        self.setMinimumSize(1000, 700)

        # --- STATE VARIABLES ---
        self.api_key = get_gemini_key()
        self.api_key_set = bool(self.api_key)

        # Puzzle Data
        self.grid_size = 15
        self.grid = None
        self.words = set()
        self.placed_words = []
        self.unfound_words = set()

        # Solver State
        self.found_words = set()
        self.found_paths = set()
        self.hint_paths = set()
        self.selected_word = None

        # UI State
        self.bg_color = QColor(DEFAULT_BG_COLOR)
        self.fg_color = QColor(DEFAULT_FG_COLOR)
        self.current_theme_name = ""
        self.word_themes = load_themes()
        self.unsaved_changes = False
        self.dark_mode = self.load_dark_mode_preference()

        # UI Components
        self.api_worker = None
        self.puzzle_grid = None
        self.words_list = None
        self.status_bar = None
        self.dark_mode_button = None

        self.setup_ui()
        self.setup_menu()
        self.check_api_key_status()
        
        # Apply dark mode if it was saved
        if self.dark_mode:
            self.apply_dark_mode()

    def setup_ui(self):
        """Set up the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Left panel - Controls
        self.setup_control_panel(main_layout)

        # Right panel - Puzzle display
        self.setup_display_panel(main_layout)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to create word search puzzles!")

        # Apply styling
        self.apply_modern_styling()

    def setup_control_panel(self, parent_layout):
        """Set up the left control panel."""
        # Create scroll area for controls
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(420)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        control_layout.setSpacing(10)

        # Add sections
        self.setup_api_key_section(control_layout)
        self.setup_topic_section(control_layout)
        self.setup_themes_section(control_layout)
        self.setup_words_and_size_section(control_layout)
        self.setup_buttons_section(control_layout)

        # Add stretch to push everything up
        control_layout.addStretch()

        scroll_area.setWidget(control_widget)
        parent_layout.addWidget(scroll_area)

    def setup_api_key_section(self, parent_layout):
        """Set up API key management section."""
        api_group = QGroupBox("🔑 Gemini API Key")
        api_layout = QVBoxLayout(api_group)

        if not self.api_key_set:
            key_layout = QHBoxLayout()
            key_layout.addWidget(QLabel("Enter Key:"))
            self.api_key_input = QLineEdit()
            self.api_key_input.setEchoMode(QLineEdit.Password)
            key_layout.addWidget(self.api_key_input)

            save_btn = QPushButton("Save Key")
            save_btn.clicked.connect(self.save_api_key)
            save_btn.setStyleSheet(f"background-color: {SUCCESS_COLOR}; color: white; padding: 5px;")
            key_layout.addWidget(save_btn)

            api_layout.addLayout(key_layout)
        else:
            success_label = QLabel("✓ API Key configured")
            success_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-weight: bold;")
            api_layout.addWidget(success_label)

        parent_layout.addWidget(api_group)

    def setup_topic_section(self, parent_layout):
        """Set up topic-based word generation section."""
        from PySide6.QtWidgets import QGridLayout
        topic_group = QGroupBox("💬 Generate from Topic")
        topic_layout = QGridLayout(topic_group)

        topic_layout.addWidget(QLabel("Topic:"), 0, 0)
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("e.g., Space, Food, Sports...")
        topic_layout.addWidget(self.topic_input, 0, 1, 1, 2)

        topic_layout.addWidget(QLabel("Num Words:"), 1, 0)
        self.num_words_spin = QSpinBox()
        self.num_words_spin.setRange(MIN_WORDS_COUNT, MAX_WORDS_COUNT)
        self.num_words_spin.setValue(10)
        topic_layout.addWidget(self.num_words_spin, 1, 1)

        self.fetch_btn = QPushButton("Fetch Words")
        self.fetch_btn.clicked.connect(self.fetch_topic_words_threaded)
        self.fetch_btn.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: white; padding: 8px;")
        topic_layout.addWidget(self.fetch_btn, 1, 2)

        parent_layout.addWidget(topic_group)

    def setup_themes_section(self, parent_layout):
        """Set up themes section."""
        themes_group = QGroupBox("🎨 Themes")
        themes_layout = QVBoxLayout(themes_group)

        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Select Theme:"))
        self.theme_combo = QComboBox()
        # Add blank option at top for creating new themes
        self.theme_combo.addItem("")
        for theme_name in sorted(self.word_themes.keys()):
            self.theme_combo.addItem(theme_name)

        theme_layout.addWidget(self.theme_combo)

        load_btn = QPushButton("Load Theme")
        load_btn.clicked.connect(self.load_theme)
        theme_layout.addWidget(load_btn)

        themes_layout.addLayout(theme_layout)

        # Buttons row for Save and Delete
        buttons_layout = QHBoxLayout()
        
        save_theme_btn = QPushButton("Save as Theme")
        save_theme_btn.clicked.connect(self.save_as_theme)
        buttons_layout.addWidget(save_theme_btn)

        delete_theme_btn = QPushButton("Delete Theme")
        delete_theme_btn.clicked.connect(self.delete_theme)
        buttons_layout.addWidget(delete_theme_btn)

        themes_layout.addLayout(buttons_layout)

        parent_layout.addWidget(themes_group)

    def setup_words_and_size_section(self, parent_layout):
        """Set up custom words and grid size sections side by side."""
        # Create horizontal layout for the row
        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)
        
        # Custom Words section (takes 3/4 of the width)
        words_group = QGroupBox("📝 Custom Words (One per line)")
        words_layout = QVBoxLayout(words_group)

        self.words_text = QTextEdit()
        self.words_text.setPlaceholderText("Enter words here...\nOne word per line")
        self.words_text.setMinimumHeight(200)  # Make it taller
        # Start with empty words list (no theme selected)

        words_layout.addWidget(self.words_text)
        
        # Grid Size section (takes 1/4 of the width)
        size_group = QGroupBox("📏 Grid Size")
        size_layout = QVBoxLayout(size_group)
        
        # Size value label
        self.size_label = QLabel(f"Size: 15x15")
        self.size_label.setAlignment(Qt.AlignCenter)
        size_layout.addWidget(self.size_label)
        
        # Slider for grid size
        from PySide6.QtWidgets import QSlider
        self.size_slider = QSlider(Qt.Vertical)
        self.size_slider.setRange(MIN_GRID_SIZE, MAX_GRID_SIZE)
        self.size_slider.setValue(15)
        self.size_slider.setTickPosition(QSlider.TicksBelow)
        self.size_slider.setTickInterval(5)
        self.size_slider.valueChanged.connect(self.on_size_changed)
        size_layout.addWidget(self.size_slider)
        
        # SpinBox for precise control
        self.size_spin = QSpinBox()
        self.size_spin.setRange(MIN_GRID_SIZE, MAX_GRID_SIZE)
        self.size_spin.setValue(15)
        self.size_spin.valueChanged.connect(self.on_size_spin_changed)
        size_layout.addWidget(self.size_spin)
        
        # Add to row with stretch factors (3:1 ratio)
        row_layout.addWidget(words_group, 3)
        row_layout.addWidget(size_group, 1)
        
        parent_layout.addLayout(row_layout)
    
    def on_size_changed(self, value):
        """Handle slider value change."""
        self.size_spin.setValue(value)
        self.size_label.setText(f"Size: {value}x{value}")
        self.grid_size = value
    
    def on_size_spin_changed(self, value):
        """Handle spin box value change."""
        self.size_slider.setValue(value)
        self.size_label.setText(f"Size: {value}x{value}")
        self.grid_size = value

    def setup_buttons_section(self, parent_layout):
        """Set up action buttons section."""
        buttons_group = QGroupBox("🎮 Actions")
        buttons_layout = QVBoxLayout(buttons_group)

        # Row 1: Generate, Save, Load, Clear
        row1 = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setStyleSheet(f"background-color: {ACCENT_COLOR}; color: white; font-weight: bold; padding: 8px;")
        self.generate_btn.clicked.connect(self.generate_puzzle)

        save_btn = QPushButton("Save Puzzle")
        save_btn.clicked.connect(self.save_puzzle)

        load_btn = QPushButton("Load Puzzle")
        load_btn.clicked.connect(self.load_puzzle)

        clear_btn = QPushButton("Clear Puzzle")
        clear_btn.clicked.connect(self.clear_puzzle)

        row1.addWidget(self.generate_btn)
        row1.addWidget(save_btn)
        row1.addWidget(load_btn)
        row1.addWidget(clear_btn)

        # Row 2: Export buttons
        row2 = QHBoxLayout()
        export_png_btn = QPushButton("Export PNG")
        export_png_btn.clicked.connect(self.export_png)

        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.clicked.connect(self.export_pdf)

        row2.addWidget(export_png_btn)
        row2.addWidget(export_pdf_btn)

        # Row 3: Color pickers
        row3 = QHBoxLayout()
        bg_color_btn = QPushButton("Background Color")
        bg_color_btn.clicked.connect(self.choose_bg_color)

        text_color_btn = QPushButton("Text Color")
        text_color_btn.clicked.connect(self.choose_text_color)

        row3.addWidget(bg_color_btn)
        row3.addWidget(text_color_btn)

        # Row 4: Dark mode toggle and About button
        row4 = QHBoxLayout()
        self.dark_mode_btn = QPushButton("🌙 Dark Mode")
        self.dark_mode_btn.setCheckable(True)
        self.dark_mode_btn.clicked.connect(self.toggle_dark_mode)

        about_btn = QPushButton("About")
        about_btn.clicked.connect(self.show_about)

        row4.addWidget(self.dark_mode_btn)
        row4.addWidget(about_btn)

        buttons_layout.addLayout(row1)
        buttons_layout.addLayout(row2)
        buttons_layout.addLayout(row3)
        buttons_layout.addLayout(row4)

        parent_layout.addWidget(buttons_group)

    def setup_display_panel(self, parent_layout):
        """Set up the right display panel with puzzle grid and word lists."""
        display_panel = QWidget()
        display_layout = QVBoxLayout(display_panel)
        display_layout.setSpacing(10)
        display_layout.setContentsMargins(0, 0, 0, 0)

        # Puzzle grid
        self.puzzle_grid = PuzzleGrid()
        self.puzzle_grid.word_selected.connect(self.on_word_selected)
        self.puzzle_grid.puzzle_clicked.connect(self.on_puzzle_clicked)

        # Word lists container (will be populated dynamically)
        self.words_list_container = QWidget()
        self.words_list_layout = QHBoxLayout(self.words_list_container)
        self.words_list_layout.setSpacing(10)
        self.words_list_layout.setContentsMargins(0, 0, 0, 0)

        # Buttons on the right side
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()  # Push buttons to the right

        hint_btn = QPushButton("Hint")
        hint_btn.clicked.connect(self.give_hint)
        hint_btn.setStyleSheet("padding: 8px 15px;")

        clear_hints_btn = QPushButton("Clear Hints")
        clear_hints_btn.clicked.connect(self.clear_hints)
        clear_hints_btn.setStyleSheet("padding: 8px 15px;")

        buttons_layout.addWidget(hint_btn)
        buttons_layout.addWidget(clear_hints_btn)

        display_layout.addWidget(self.puzzle_grid, 3)
        display_layout.addWidget(self.words_list_container, 1)
        display_layout.addLayout(buttons_layout)

        parent_layout.addWidget(display_panel, 1)

    def create_word_lists(self):
        """Create word list widgets dynamically with max 10 words per column."""
        # Clear existing word lists
        while self.words_list_layout.count():
            child = self.words_list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.words:
            return

        # Calculate words per column (max 10)
        max_words_per_column = 10
        num_columns = (len(self.words) + max_words_per_column - 1) // max_words_per_column

        sorted_words = sorted(self.words)
        for col_idx in range(num_columns):
            word_list = QListWidget()
            word_list.setMaximumHeight(200)

            # Add words for this column
            start_idx = col_idx * max_words_per_column
            end_idx = min(start_idx + max_words_per_column, len(sorted_words))

            for word in sorted_words[start_idx:end_idx]:
                item = QListWidgetItem(word)
                if word in self.found_words:
                    item.setForeground(QColor(SUCCESS_COLOR))
                word_list.addItem(item)

            word_list.itemClicked.connect(self.on_word_clicked)
            self.words_list_layout.addWidget(word_list)

    def setup_menu(self):
        """Set up the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        save_action = QAction("Save Puzzle", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_puzzle)
        file_menu.addAction(save_action)

        load_action = QAction("Load Puzzle", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_puzzle)
        file_menu.addAction(load_action)

        file_menu.addSeparator()

        export_png_action = QAction("Export PNG", self)
        export_png_action.triggered.connect(self.export_png)
        file_menu.addAction(export_png_action)

        export_pdf_action = QAction("Export PDF", self)
        export_pdf_action.triggered.connect(self.export_pdf)
        file_menu.addAction(export_pdf_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def apply_modern_styling(self):
        """Apply modern styling to the application."""
        if self.dark_mode:
            # Dark mode stylesheet
            self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {DARK_BG_COLOR};
            }}
            QWidget {{
                background-color: {DARK_BG_COLOR};
                color: {DARK_FG_COLOR};
            }}
            QLabel {{
                background-color: transparent;
                color: {DARK_FG_COLOR};
            }}
            QGroupBox {{
                background-color: #353535;
                border: 2px solid #505050;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: {DARK_FG_COLOR};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            QPushButton {{
                background-color: {DARK_BUTTON_BG};
                color: {DARK_BUTTON_FG};
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #4A4A4A;
                border: 1px solid #666;
            }}
            QPushButton:pressed {{
                background-color: #2A2A2A;
            }}
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                background-color: #353535;
                color: {DARK_FG_COLOR};
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
            }}
            QListWidget {{
                background-color: #353535;
                color: {DARK_FG_COLOR};
                border: 1px solid #555;
                border-radius: 4px;
            }}
            QStatusBar {{
                background-color: #353535;
                color: {DARK_FG_COLOR};
            }}
            QMenuBar {{
                background-color: #353535;
                color: {DARK_FG_COLOR};
            }}
            QMenuBar::item:selected {{
                background-color: #4A4A4A;
            }}
            QMenu {{
                background-color: #353535;
                color: {DARK_FG_COLOR};
                border: 1px solid #555;
            }}
            QMenu::item:selected {{
                background-color: #4A4A4A;
            }}
            """)
        else:
            # Light mode stylesheet
            self.setStyleSheet(f"""
            QGroupBox {{
                background-color: white;
                border: 2px solid {ACCENT_COLOR};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }}
            QPushButton {{
                background-color: {ACCENT_COLOR};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #0056B3;
            }}
            QPushButton:pressed {{
                background-color: #004085;
            }}
            QLineEdit, QTextEdit, QSpinBox, QComboBox {{
                border: 1px solid #CED4DA;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }}
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 2px solid {ACCENT_COLOR};
            }}
            QListWidget {{
                border: 1px solid #CED4DA;
                border-radius: 4px;
                background-color: white;
            }}
            """)

    def check_api_key_status(self):
        """Check if API key is configured and update UI."""
        pass  # API key status is checked during initialization

    def load_dark_mode_preference(self):
        """Load dark mode preference from config.json."""
        import os
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('dark_mode', False)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return False

    def save_dark_mode_preference(self):
        """Save dark mode preference to config.json."""
        import os
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            
            config['dark_mode'] = self.dark_mode
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save dark mode preference: {e}")

    def save_api_key(self):
        """Save the entered API key."""
        key = self.api_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Empty Key", "Please enter an API key.")
            return

        if save_gemini_key(key):
            self.api_key = key
            self.api_key_set = True
            QMessageBox.information(self, "Success", "API key saved successfully!")
            self.status_bar.showMessage("✓ API key configured")
        else:
            QMessageBox.critical(self, "Error", "Failed to save API key.")

    def fetch_topic_words_threaded(self):
        """Fetch words from Gemini API using a worker thread."""
        if not self.api_key:
            QMessageBox.warning(self, "No API Key", "Please configure your Gemini API key first.")
            return

        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "No Topic", "Please enter a topic.")
            return

        num_words = self.num_words_spin.value()

        # Disable controls during API call
        self.set_controls_enabled(False)
        self.status_bar.showMessage(f"🔄 Fetching {num_words} words about '{topic}'...")

        # Create and start worker thread
        self.api_worker = ApiWorker(self.api_key, topic, num_words)
        self.api_worker.finished.connect(self.on_words_fetched)
        self.api_worker.error.connect(self.on_fetch_error)
        self.api_worker.start()

    def on_words_fetched(self, words, topic):
        """Handle successful word fetch from API."""
        self.set_controls_enabled(True)

        if words:
            self.words_text.setPlainText('\n'.join(words))
            self.status_bar.showMessage(f"✓ Fetched {len(words)} words for topic: {topic}")
            QMessageBox.information(self, "Success", f"Fetched {len(words)} words for '{topic}'!")
        else:
            self.status_bar.showMessage("⚠️ No valid words found")
            QMessageBox.warning(self, "No Words", "No valid words were returned by the API.")

    def on_fetch_error(self, error_msg):
        """Handle error from API worker thread."""
        self.set_controls_enabled(True)
        self.status_bar.showMessage("❌ API call failed")
        QMessageBox.critical(self, "API Error", f"Failed to fetch words:\n{error_msg}")

    def set_controls_enabled(self, enabled):
        """Enable or disable controls during API calls."""
        self.fetch_btn.setEnabled(enabled)
        self.generate_btn.setEnabled(enabled)
        self.topic_input.setEnabled(enabled)
        self.num_words_spin.setEnabled(enabled)

    def load_theme(self):
        """Load a theme from the dropdown."""
        theme_name = self.theme_combo.currentText()
        if not theme_name:  # Blank selection
            return

        if theme_name in self.word_themes:
            words = self.word_themes[theme_name]
            self.words_text.setPlainText('\n'.join(words))
            self.current_theme_name = theme_name
            self.status_bar.showMessage(f"✓ Loaded theme: {theme_name}")

    def save_as_theme(self):
        """Save current words as a theme."""
        words_text = self.words_text.toPlainText().strip()
        if not words_text:
            QMessageBox.warning(self, "No Words", "Please enter some words first.")
            return

        # Get the current theme name from combo box
        current_name = self.theme_combo.currentText()

        # If there's a selected theme, ask if they want to overwrite or create new
        if current_name:
            reply = QMessageBox.question(
                self,
                "Save Theme",
                f"Do you want to overwrite the existing theme '{current_name}'?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )

            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                theme_name = current_name
            else:  # No - create new theme
                theme_name, ok = QInputDialog.getText(self, "New Theme", "Enter a new theme name:")
                if not ok or not theme_name.strip():
                    return
                theme_name = theme_name.strip()
        else:
            # No theme selected, ask for a name
            theme_name, ok = QInputDialog.getText(self, "Save Theme", "Enter theme name:")
            if not ok or not theme_name.strip():
                return
            theme_name = theme_name.strip()

        # Save the theme
        words_list = words_text.split('\n')
        validated = validate_words(words_list)

        if not validated:
            QMessageBox.warning(self, "Invalid Words", "No valid words to save.")
            return

        self.word_themes[theme_name] = validated
        save_themes(self.word_themes)

        # Update combo box if needed
        if theme_name not in [self.theme_combo.itemText(i) for i in range(self.theme_combo.count())]:
            self.theme_combo.addItem(theme_name)

        # Select the saved theme
        self.theme_combo.setCurrentText(theme_name)
        self.current_theme_name = theme_name

        QMessageBox.information(self, "Success", f"Theme '{theme_name}' saved!")
        self.status_bar.showMessage(f"✓ Theme '{theme_name}' saved")

    def delete_theme(self):
        """Delete the selected theme."""
        theme_name = self.theme_combo.currentText()
        if not theme_name:
            QMessageBox.warning(self, "No Theme", "Please select a theme to delete.")
            return

        reply = QMessageBox.question(
            self,
            "Delete Theme",
            f"Are you sure you want to delete the theme '{theme_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Remove from dict and combo box
            if theme_name in self.word_themes:
                del self.word_themes[theme_name]
                save_themes(self.word_themes)

            # Find and remove from combo box
            index = self.theme_combo.findText(theme_name)
            if index >= 0:
                self.theme_combo.removeItem(index)

            # Clear selection
            self.theme_combo.setCurrentIndex(0)  # Select blank
            self.current_theme_name = ""

            QMessageBox.information(self, "Deleted", f"Theme '{theme_name}' deleted.")
            self.status_bar.showMessage(f"✓ Theme '{theme_name}' deleted")

    def generate(self):
        """Generate a new word search puzzle."""
        words_text = self.words_text.toPlainText().strip()
        if not words_text:
            QMessageBox.warning(self, "No Words", "Please enter some words first.")
            return

        words_list = words_text.split('\n')
        validated_words = validate_words(words_list)

        if not validated_words:
            QMessageBox.warning(self, "Invalid Words", "No valid words found. Words must be 2-15 uppercase letters.")
            return

        self.grid_size = self.size_spin.value()

        # Disable controls during generation
        self.set_controls_enabled(False)
        self.status_bar.showMessage("🔄 Generating puzzle...")

        # Generate puzzle (this might take a moment for large grids)
        grid, placed_words = generate_word_search(self.grid_size, validated_words)

        self.set_controls_enabled(True)

        if grid is None:
            QMessageBox.critical(self, "Generation Failed", "Could not generate a valid puzzle. Try fewer words or a larger grid.")
            self.status_bar.showMessage("❌ Puzzle generation failed.")
            return

        # Update state
        self.grid = grid
        self.words = set(validated_words)
        self.placed_words = placed_words
        self.unfound_words = set(validated_words)
        self.found_words = set()
        self.found_paths = set()
        self.hint_paths = set()

        # Update UI
        self.puzzle_grid.set_grid(grid)
        self.update_words_list()

        self.status_bar.showMessage(f"✓ Puzzle generated! Find {len(validated_words)} words.")
        self.unsaved_changes = True

    # Alias for backward compatibility
    def generate_puzzle(self):
        """Alias for generate()."""
        self.generate()

    def update_words_list(self):
        """Update the word list display."""
        self.create_word_lists()

    def on_word_selected(self, path):
        """Handle word selection on the grid."""
        # Extract word from the path
        word = ''.join([self.grid[r][c] for r, c in path])

        # Check if it matches any word (forward or backward)
        if word in self.words and word not in self.found_words:
            self.found_words.add(word)
            self.found_paths.add(frozenset(path))
            self.unfound_words.discard(word)
            self.update_words_list()
            self.puzzle_grid.set_grid(self.grid, self.found_paths, self.hint_paths)
            self.status_bar.showMessage(f"✓ Found: {word}! ({len(self.found_words)}/{len(self.words)})")

            # Check if all words found
            if not self.unfound_words:
                QMessageBox.information(self, "🎉 Congratulations!", "You found all the words!")
                self.status_bar.showMessage("🎉 Puzzle completed!")
        else:
            # Check reverse
            word_rev = word[::-1]
            if word_rev in self.words and word_rev not in self.found_words:
                self.found_words.add(word_rev)
                self.found_paths.add(frozenset(path))
                self.unfound_words.discard(word_rev)
                self.update_words_list()
                self.puzzle_grid.set_grid(self.grid, self.found_paths, self.hint_paths)
                self.status_bar.showMessage(f"✓ Found: {word_rev}! ({len(self.found_words)}/{len(self.words)})")

                # Check if all words found
                if not self.unfound_words:
                    QMessageBox.information(self, "🎉 Congratulations!", "You found all the words!")
                    self.status_bar.showMessage("🎉 Puzzle completed!")

    def on_word_clicked(self, item):
        """Handle word clicked in the list."""
        word = item.text()
        if word in self.unfound_words:
            self.selected_word = word
            self.status_bar.showMessage(f"Selected: {word} - Click 'Hint' to reveal first letter")
        else:
            self.status_bar.showMessage(f"{word} already found!")

    def give_hint(self):
        """Give a hint for the selected word."""
        if not self.grid:
            QMessageBox.information(self, "No Puzzle", "Generate a puzzle first!")
            return

        if not self.selected_word:
            QMessageBox.information(self, "No Word Selected", "Click on a word in the list first!")
            return

        if self.selected_word in self.found_words:
            QMessageBox.information(self, "Already Found", f"You already found '{self.selected_word}'!")
            return

        # Find the selected word in placed_words
        for word_data in self.placed_words:
            if word_data['word'] == self.selected_word:
                path = word_data['path']
                # Convert path to tuples if it's a list (happens when loading from JSON)
                if path and isinstance(path[0], list):
                    path = [tuple(cell) for cell in path]
                # Highlight only the first letter
                first_cell_path = frozenset([path[0]])
                self.hint_paths = {first_cell_path}
                self.puzzle_grid.set_grid(self.grid, self.found_paths, self.hint_paths)
                self.status_bar.showMessage(f"💡 Hint: First letter of '{self.selected_word}' highlighted")
                return

        QMessageBox.warning(self, "Word Not Found", f"Could not find '{self.selected_word}' in the puzzle.")

    def clear_hints(self):
        """Clear all hint highlighting."""
        self.hint_paths = set()
        self.puzzle_grid.set_grid(self.grid, self.found_paths, self.hint_paths)

    def on_puzzle_clicked(self):
        """Handle puzzle grid clicked - clear hints and selection."""
        self.clear_hints()
        self.selected_word = None

    def toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        self.dark_mode = not self.dark_mode
        self.save_dark_mode_preference()
        self.apply_dark_mode()

    def apply_dark_mode(self):
        """Apply dark or light mode based on current setting."""
        # Apply dark mode palette to entire application
        app = QApplication.instance()
        if self.dark_mode:
            # Create dark palette
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(DARK_BG_COLOR))
            dark_palette.setColor(QPalette.WindowText, QColor(DARK_FG_COLOR))
            dark_palette.setColor(QPalette.Base, QColor("#353535"))
            dark_palette.setColor(QPalette.AlternateBase, QColor(DARK_BG_COLOR))
            dark_palette.setColor(QPalette.ToolTipBase, QColor(DARK_FG_COLOR))
            dark_palette.setColor(QPalette.ToolTipText, QColor(DARK_FG_COLOR))
            dark_palette.setColor(QPalette.Text, QColor(DARK_FG_COLOR))
            dark_palette.setColor(QPalette.Button, QColor(DARK_BUTTON_BG))
            dark_palette.setColor(QPalette.ButtonText, QColor(DARK_BUTTON_FG))
            dark_palette.setColor(QPalette.BrightText, QColor("#FF0000"))
            dark_palette.setColor(QPalette.Link, QColor("#2A82DA"))
            dark_palette.setColor(QPalette.Highlight, QColor("#2A82DA"))
            dark_palette.setColor(QPalette.HighlightedText, QColor("#000000"))
            app.setPalette(dark_palette)

            # Update grid colors
            if self.puzzle_grid:
                self.puzzle_grid.bg_color = QColor(DARK_BG_COLOR)
                self.puzzle_grid.fg_color = QColor(DARK_FG_COLOR)
                self.puzzle_grid.found_color = QColor(DARK_FOUND_COLOR)
        else:
            # Reset to default light palette
            app.setPalette(app.style().standardPalette())

            # Update grid colors
            if self.puzzle_grid:
                self.puzzle_grid.bg_color = QColor(DEFAULT_BG_COLOR)
                self.puzzle_grid.fg_color = QColor(DEFAULT_FG_COLOR)
                self.puzzle_grid.found_color = QColor(FOUND_COLOR)

        # Reapply styling
        self.apply_modern_styling()

        # Redraw grid if it exists
        if self.grid and self.puzzle_grid:
            self.puzzle_grid.redraw()

        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.showMessage(f"{'🌙 Dark' if self.dark_mode else '☀️ Light'} mode enabled")

    def choose_bg_color(self):
        """Choose background color."""
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(self.bg_color, self, "Choose Background Color")
        if color.isValid():
            self.bg_color = color
            if self.grid:
                self.puzzle_grid.set_grid(self.grid, self.found_paths, self.hint_paths)
            self.unsaved_changes = True

    def choose_text_color(self):
        """Choose text color."""
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(self.fg_color, self, "Choose Text Color")
        if color.isValid():
            self.fg_color = color
            if self.grid:
                self.puzzle_grid.set_grid(self.grid, self.found_paths, self.hint_paths)
            self.unsaved_changes = True

    def save_puzzle(self):
        """Save the current puzzle to a JSON file."""
        if not self.grid:
            QMessageBox.warning(self, "No Puzzle", "Generate a puzzle first!")
            return

        # Create saved/ folder if it doesn't exist
        import os
        saved_dir = os.path.join(os.path.dirname(__file__), 'saved')
        os.makedirs(saved_dir, exist_ok=True)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Puzzle",
            saved_dir,
            "JSON Files (*.json)"
        )

        if filename:
            # Add .json extension if not present
            if not filename.lower().endswith('.json'):
                filename += '.json'
            
            try:
                puzzle_data = {
                    'grid': self.grid,
                    'words': list(self.words),
                    'placed_words': self.placed_words,
                    'grid_size': self.grid_size
                }

                with open(filename, 'w') as f:
                    json.dump(puzzle_data, f, indent=4)

                QMessageBox.information(self, "Success", "Puzzle saved successfully!")
                self.status_bar.showMessage(f"✓ Puzzle saved to {filename}")
                self.unsaved_changes = False
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save puzzle:\n{e}")

    def load_puzzle(self):
        """Load a puzzle from a JSON file."""
        # Create saved/ folder if it doesn't exist
        import os
        saved_dir = os.path.join(os.path.dirname(__file__), 'saved')
        os.makedirs(saved_dir, exist_ok=True)

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Load Puzzle",
            saved_dir,
            "JSON Files (*.json)"
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    puzzle_data = json.load(f)

                self.grid = puzzle_data['grid']
                self.words = set(puzzle_data['words'])
                self.placed_words = puzzle_data['placed_words']
                
                # Convert paths from lists to tuples (JSON stores tuples as lists)
                for word_data in self.placed_words:
                    if 'path' in word_data and word_data['path']:
                        if isinstance(word_data['path'][0], list):
                            word_data['path'] = [tuple(cell) for cell in word_data['path']]
                    if 'direction' in word_data and isinstance(word_data['direction'], list):
                        word_data['direction'] = tuple(word_data['direction'])
                
                self.grid_size = puzzle_data['grid_size']

                # Reset solver state
                self.unfound_words = set(self.words)
                self.found_words = set()
                self.found_paths = set()
                self.hint_paths = set()

                # Update UI
                self.size_spin.setValue(self.grid_size)
                self.words_text.setPlainText('\n'.join(sorted(self.words)))
                self.puzzle_grid.set_grid(self.grid)
                self.update_words_list()

                QMessageBox.information(self, "Success", "Puzzle loaded successfully!")
                self.status_bar.showMessage(f"✓ Puzzle loaded from {filename}")
                self.unsaved_changes = False
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load puzzle:\n{e}")

    def clear_all(self):
        """Clear all input and reset the puzzle."""
        reply = QMessageBox.question(
            self,
            "Clear All",
            "Are you sure you want to clear everything?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.words_text.clear()
            self.topic_input.clear()
            self.theme_combo.setCurrentIndex(0)
            self.grid = None
            self.words = set()
            self.placed_words = []
            self.unfound_words = set()
            self.found_words = set()
            self.found_paths = set()
            self.hint_paths = set()
            self.selected_word = None
            self.puzzle_grid.set_grid(None)
            self.update_words_list()
            self.status_bar.showMessage("🧹 All cleared")
            self.unsaved_changes = False

    # Alias for backward compatibility
    def clear_puzzle(self):
        """Alias for clear_all()."""
        self.clear_all()

    def export_png(self):
        """Export puzzle to PNG file."""
        if not self.grid:
            QMessageBox.warning(self, "No Puzzle", "Generate a puzzle first!")
            return

        # Create exported/ folder if it doesn't exist
        import os
        exported_dir = os.path.join(os.path.dirname(__file__), 'exported')
        os.makedirs(exported_dir, exist_ok=True)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to PNG",
            exported_dir,
            "PNG Files (*.png)"
        )

        if filename:
            # Add .png extension if not present
            if not filename.lower().endswith('.png'):
                filename += '.png'
            
            try:
                export_grid_to_png(self.grid, self.grid_size, self.bg_color, self.fg_color, filename)
                QMessageBox.information(self, "Success", "Puzzle exported to PNG!")
                self.status_bar.showMessage(f"✓ Exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export PNG:\n{e}")

    def export_pdf(self):
        """Export puzzle to PDF file."""
        if not self.grid:
            QMessageBox.warning(self, "No Puzzle", "Generate a puzzle first!")
            return

        # Create exported/ folder if it doesn't exist
        import os
        exported_dir = os.path.join(os.path.dirname(__file__), 'exported')
        os.makedirs(exported_dir, exist_ok=True)

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export to PDF",
            exported_dir,
            "PDF Files (*.pdf)"
        )

        if filename:
            # Add .pdf extension if not present
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            try:
                export_grid_to_pdf(self.grid, self.grid_size, self.words, filename)
                QMessageBox.information(self, "Success", "Puzzle exported to PDF!")
                self.status_bar.showMessage(f"✓ Exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export PDF:\n{e}")

    def show_about(self):
        """Show about dialog."""
        about_text = """
        <h2>WordSeeker</h2>
        <p><b>Version:</b> 1.0</p>
        <p><b>Author:</b> Quantum Pixelator</p>
        <p>Create custom word search puzzles with ease!</p>
        <p>Features:</p>
        <ul>
            <li>AI-powered word generation</li>
            <li>Custom themes</li>
            <li>Dark mode support</li>
            <li>PNG & PDF export</li>
        </ul>
        """
        QMessageBox.about(self, "About Word Search Creator", about_text)

    def closeEvent(self, event):
        """Handle window close event."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.No:
                event.ignore()
                return

        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("WordSeeker") 
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Quantum Pixelator")

    # Create and show main window
    window = WordSearchApp()
    window.show()

    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
