"""
Puzzle generation engine for Word Search Creator.
Handles word placement, grid generation, and validation.
"""

import random
from constants import DIRECTIONS, MAX_PLACEMENT_ATTEMPTS


def generate_word_search(grid_size, words):
    """
    Generates a word search puzzle grid with the given words placed randomly.
    
    Args:
        grid_size (int): Size of the square grid (e.g., 15 for 15x15)
        words (list): List of words to place in the grid
        
    Returns:
        tuple: (grid, placed_words) where grid is a 2D list and placed_words is a list of dicts
               Returns (None, None) if placement fails after max attempts
    """
    # Filter out words that are too long to fit in the grid
    valid_words = [w for w in words if len(w) <= grid_size]
    
    # If any words were filtered out, we'll fail the generation
    if len(valid_words) < len(words):
        return None, None
    
    # Initialize empty grid filled with spaces
    grid = [[' ' for _ in range(grid_size)] for _ in range(grid_size)]
    placed_words = []
    
    # Sort words by length (longest first) for better placement success
    sorted_words = sorted(valid_words, key=len, reverse=True)
    
    for word in sorted_words:
        placed = False
        attempts = 0
        
        while not placed and attempts < MAX_PLACEMENT_ATTEMPTS:
            # Choose random starting position and direction
            start_row = random.randint(0, grid_size - 1)
            start_col = random.randint(0, grid_size - 1)
            direction = random.choice(DIRECTIONS)
            
            # Check if word fits in this position/direction
            if can_place_word(grid, word, start_row, start_col, direction):
                # Place the word
                place_word(grid, word, start_row, start_col, direction)
                placed_words.append({
                    'word': word,
                    'path': get_word_path(word, start_row, start_col, direction),
                    'direction': direction
                })
                placed = True
            
            attempts += 1
        
        if not placed:
            # Failed to place this word
            return None, None
    
    # Fill empty cells with random letters
    fill_empty_cells(grid)
    
    return grid, placed_words


def can_place_word(grid, word, start_row, start_col, direction):
    """
    Checks if a word can be placed at the given position in the given direction.
    
    Args:
        grid: 2D list representing the grid
        word (str): Word to place
        start_row, start_col: Starting position
        direction: Tuple (dr, dc) for direction
        
    Returns:
        bool: True if placement is possible
    """
    dr, dc = direction
    size = len(grid)
    
    for i, letter in enumerate(word):
        row = start_row + i * dr
        col = start_col + i * dc
        
        # Check bounds
        if not (0 <= row < size and 0 <= col < size):
            return False
        
        # Check if cell is empty or contains the same letter
        if grid[row][col] != ' ' and grid[row][col] != letter:
            return False
    
    return True


def place_word(grid, word, start_row, start_col, direction):
    """
    Places a word on the grid at the given position in the given direction.
    
    Args:
        grid: 2D list representing the grid
        word (str): Word to place
        start_row, start_col: Starting position
        direction: Tuple (dr, dc) for direction
    """
    dr, dc = direction
    
    for i, letter in enumerate(word):
        row = start_row + i * dr
        col = start_col + i * dc
        grid[row][col] = letter


def get_word_path(word, start_row, start_col, direction):
    """
    Gets the path (list of (row, col) tuples) for a word placement.
    
    Args:
        word (str): The word
        start_row, start_col: Starting position
        direction: Tuple (dr, dc) for direction
        
    Returns:
        list: List of (row, col) tuples representing the word path
    """
    dr, dc = direction
    path = []
    
    for i in range(len(word)):
        row = start_row + i * dr
        col = start_col + i * dc
        path.append((row, col))
    
    return path


def fill_empty_cells(grid):
    """
    Fills all empty cells (' ') in the grid with random uppercase letters.
    
    Args:
        grid: 2D list representing the grid
    """
    for row in range(len(grid)):
        for col in range(len(grid[row])):
            if grid[row][col] == ' ':
                grid[row][col] = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
