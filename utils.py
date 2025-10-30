"""
Utility functions for Word Search Creator application.
Includes API handling, file I/O, validation, and theme management.
"""

import json
import os
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMessageBox

from constants import (
    CONFIG_FILE, THEMES_FILE, DEFAULT_THEMES_DATA,
    MIN_WORD_LEN, MAX_WORD_LEN, MAX_WORDS_COUNT, API_TIMEOUT
)

# Google Generative AI (optional)
try:
    import google.generativeai as genai
except ImportError:
    genai = None


# --- API KEY MANAGEMENT ---

def get_gemini_key():
    """Loads Gemini API key from config.json or environment variables."""
    # 1. Check environment variable
    key = os.getenv('GEMINI_API_KEY')
    if key:
        return key

    # 2. Check config file
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get('GEMINI_API_KEY')
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def save_gemini_key(key):
    """Saves Gemini API key to config.json."""
    try:
        config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)

        config['GEMINI_API_KEY'] = key

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        QMessageBox.critical(None, "Save Error", f"Could not save API key to {CONFIG_FILE}: {e}")
        return False


# --- THEME MANAGEMENT ---

def load_themes():
    """Loads custom themes from themes.json, merging with defaults."""
    themes = DEFAULT_THEMES_DATA.copy()
    try:
        with open(THEMES_FILE, 'r') as f:
            custom_themes = json.load(f)
            themes.update(custom_themes)
    except (FileNotFoundError, json.JSONDecodeError):
        # File doesn't exist or is empty/corrupt, use defaults
        pass
    return themes


def save_themes(themes):
    """Saves current theme list (excluding defaults) to themes.json."""
    # Only save custom themes (i.e., not in DEFAULT_THEMES_DATA)
    custom_themes = {k: v for k, v in themes.items() if k not in DEFAULT_THEMES_DATA}
    try:
        with open(THEMES_FILE, 'w') as f:
            json.dump(custom_themes, f, indent=4)
        return True
    except Exception as e:
        QMessageBox.critical(None, "Save Error", f"Could not save themes to {THEMES_FILE}: {e}")
        return False


# --- WORD VALIDATION ---

def validate_words(words_list):
    """Validates and filters a list of words according to constraints."""
    validated = []
    for word in words_list:
        word = word.strip().upper()
        # Check length constraints
        if not (MIN_WORD_LEN <= len(word) <= MAX_WORD_LEN):
            continue
        # Check for only uppercase letters
        if not word.isalpha() or not word.isupper():
            continue
        # Check for duplicates (case-insensitive)
        if word in [w.upper() for w in validated]:
            continue
        validated.append(word)

    return validated[:MAX_WORDS_COUNT]  # Limit to max words


# --- API FUNCTIONS ---

def fetch_topic_words(api_key, topic, num_words):
    """
    Calls the Gemini API to get topic-related words.
    Returns list of validated words or raises exception.
    """
    if not genai:
        raise ImportError("Google Generative AI library not available")

    # Configure the API with the loaded key
    genai.configure(api_key=api_key)

    # Try different model names in order of preference
    model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash-exp']
    model = None

    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            # Test the model with a simple request
            test_response = model.generate_content(
                "Test", 
                generation_config=genai.types.GenerationConfig(max_output_tokens=1)
            )
            break  # If we get here, the model works
        except Exception:
            continue  # Try next model

    if model is None:
        raise ValueError("No available Gemini models found. Please check your API key and library version.")

    prompt = (
        f"List exactly {num_words} unique uppercase English words "
        f"(2-15 letters each) directly related to '{topic}'. "
        f"One word per line. No explanations, numbers, or extras."
    )

    # Generate content using the model
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=500,
        ),
        request_options={"timeout": API_TIMEOUT}
    )

    if not response.text:
        raise ValueError("API returned an empty response.")

    raw_words = response.text.strip().split('\n')
    validated_words = validate_words(raw_words)

    return validated_words


# --- WORKER THREAD FOR API CALLS ---

class ApiWorker(QThread):
    """Worker thread for API calls to prevent UI blocking."""
    finished = Signal(list, str)  # words, topic
    error = Signal(str)  # error message

    def __init__(self, api_key, topic, num_words):
        super().__init__()
        self.api_key = api_key
        self.topic = topic
        self.num_words = num_words

    def run(self):
        try:
            words = fetch_topic_words(self.api_key, self.topic, self.num_words)
            self.finished.emit(words, self.topic)
        except Exception as e:
            self.error.emit(str(e))
