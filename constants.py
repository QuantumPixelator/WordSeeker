"""
Configuration constants for WordSeeker application.
"""

# --- FILE PATHS ---
CONFIG_FILE = 'config.json'
THEMES_FILE = 'themes.json'

# Default theme data
DEFAULT_THEMES_DATA = {
    'Halloween': ['GHOST', 'WITCH', 'PUMPKIN', 'SPOOKY', 'ZOMBIE', 'BAT', 'COSTUME', 'TRICKORTREAT'],
    'Christmas': ['SANTA', 'ELF', 'REINDEER', 'MISTLETOE', 'JINGLEBELLS', 'EGGNOG', 'CANDYCANE', 'STOCKING'],
    'Faith': ['PRAYER', 'GRACE', 'HOPE', 'FAITH', 'LOVE', 'PEACE', 'JOY', 'BIBLE'],
    'Motorsports': ['FORMULAONE', 'NASCAR', 'RALLY', 'DRIFT', 'TURBO', 'PITSTOP', 'CHECKEREDFLAG', 'SPEEDWAY']
}

# --- GRID & WORD CONSTRAINTS ---
MIN_GRID_SIZE = 10
MAX_GRID_SIZE = 25
MIN_WORDS_COUNT = 4
MAX_WORDS_COUNT = 15
MIN_WORD_LEN = 2
MAX_WORD_LEN = 15
MAX_GENERATION_ATTEMPTS = 50
MAX_PLACEMENT_ATTEMPTS = 100

# --- WORD PLACEMENT DIRECTIONS ---
# 8 possible directions: horizontal, vertical, diagonal
DIRECTIONS = [
    (0, 1),   # Right
    (1, 0),   # Down
    (0, -1),  # Left
    (-1, 0),  # Up
    (1, 1),   # Down-right
    (1, -1),  # Down-left
    (-1, 1),  # Up-right
    (-1, -1)  # Up-left
]

# --- UI CONSTANTS ---
WINDOW_TITLE = "WordSeeker"
CELL_SIZE = 30
PNG_CELL_SIZE = 50

# --- LIGHT MODE COLORS ---
DEFAULT_BG_COLOR = '#F8F9FA'  # Modern light gray
DEFAULT_FG_COLOR = '#212529'  # Dark gray
HINT_COLOR = '#FFF3CD'  # Light yellow
FOUND_COLOR = '#C8E6C9'  # Pale green background for found words
TEMP_DRAG_COLOR = '#CCE5FF'  # Light blue for selection
ACCENT_COLOR = '#007BFF'  # Modern blue
SUCCESS_COLOR = '#28A745'  # Green
WARNING_COLOR = '#FFC107'  # Amber
ERROR_COLOR = '#DC3545'  # Red

# --- DARK MODE COLORS ---
DARK_BG_COLOR = "#2B2B2B"
DARK_FG_COLOR = "#FFFFFF"
DARK_FOUND_COLOR = '#4A5F4A'  # Dark mode pale green
DARK_BUTTON_BG = "#404040"
DARK_BUTTON_FG = "#FFFFFF"

# --- API CONFIGURATION ---
API_TIMEOUT = 30  # seconds (increased for better reliability)

# --- EXPORT SETTINGS ---
PDF_SCALE = 0.5
