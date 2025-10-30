"""
Custom widgets for Word Search Creator application.
"""

from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPen, QBrush

from constants import CELL_SIZE, DEFAULT_BG_COLOR, DEFAULT_FG_COLOR, HINT_COLOR, FOUND_COLOR, TEMP_DRAG_COLOR


class PuzzleGrid(QGraphicsView):
    """Custom widget for displaying and interacting with the word search grid."""

    word_selected = Signal(list)  # Emitted when a word path is selected
    puzzle_clicked = Signal()  # Emitted when the puzzle grid is clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.grid_size = 15
        self.cell_size = CELL_SIZE
        self.grid = None
        self.bg_color = QColor(DEFAULT_BG_COLOR)
        self.fg_color = QColor(DEFAULT_FG_COLOR)
        self.hint_color = QColor("#FFD700")  # Bright gold for hints
        self.found_color = QColor(FOUND_COLOR)
        self.temp_drag_color = QColor(TEMP_DRAG_COLOR)

        # Interaction state
        self.is_dragging = False
        self.drag_start_cell = None
        self.drag_current_cell = None
        self.current_temp_path = []
        self.found_paths = set()  # frozenset of (r,c) tuples
        self.hint_paths = set()  # frozenset of (r,c) tuples

        self.setMinimumSize(400, 400)  # Base minimum size
        self.setStyleSheet("border: 1px solid #ccc;")

    def set_grid(self, grid, found_paths=None, hint_paths=None):
        """Update the displayed grid."""
        self.grid = grid
        self.grid_size = len(grid) if grid else 15
        self.found_paths = found_paths or set()
        self.hint_paths = hint_paths or set()

        # Adjust minimum size based on grid size
        min_size = max(400, self.grid_size * self.cell_size + 100)
        self.setMinimumSize(min_size, min_size)

        self.redraw()

        # Ensure the view is centered on the grid
        if self.grid:
            grid_width = self.grid_size * self.cell_size
            grid_height = self.grid_size * self.cell_size
            self.centerOn(grid_width / 2, grid_height / 2)

    def redraw(self):
        """Redraw the entire grid."""
        self.scene.clear()

        if not self.grid:
            return

        # Calculate grid dimensions
        grid_width = self.grid_size * self.cell_size
        grid_height = self.grid_size * self.cell_size

        # Set scene rectangle to center the grid in the view
        # The scene will be larger than the grid to allow for centering
        scene_margin = 50  # Extra space around the grid
        self.scene.setSceneRect(-scene_margin, -scene_margin,
                               grid_width + 2 * scene_margin,
                               grid_height + 2 * scene_margin)

        # Center the view on the grid
        self.centerOn(grid_width / 2, grid_height / 2)

        # Draw cells
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x = c * self.cell_size
                y = r * self.cell_size

                # Determine cell color - check if this cell is part of any found or hint path
                bg_color = self.bg_color
                
                # Check if cell is part of any found word path
                for path in self.found_paths:
                    if (r, c) in path:
                        bg_color = self.found_color
                        break
                
                # Check if cell is part of any hint path (overrides found color)
                for path in self.hint_paths:
                    if (r, c) in path:
                        bg_color = self.hint_color
                        break

                # Create cell rectangle
                rect = QGraphicsRectItem(x, y, self.cell_size, self.cell_size)
                rect.setBrush(QBrush(bg_color))
                rect.setPen(QPen(QColor('#ddd'), 1))
                self.scene.addItem(rect)

                # Add letter text
                if self.grid[r][c] != ' ':
                    text = self.scene.addText(self.grid[r][c])
                    text.setPos(x + self.cell_size/2 - 5, y + self.cell_size/2 - 8)
                    text.setDefaultTextColor(self.fg_color)

        # Draw temporary drag path as a line
        if self.current_temp_path:
            self.draw_path(self.current_temp_path, self.temp_drag_color, 3)

        # Note: Found words are now shown with highlighted cell backgrounds (no lines)
        # Hints are shown with highlighted cell backgrounds (no lines)

    def draw_path(self, path, color, width):
        """Draw a highlighted path on the grid."""
        if len(path) < 2:
            return

        pen = QPen(color, width)
        for i in range(len(path) - 1):
            r1, c1 = path[i]
            r2, c2 = path[i + 1]
            x1 = c1 * self.cell_size + self.cell_size / 2
            y1 = r1 * self.cell_size + self.cell_size / 2
            x2 = c2 * self.cell_size + self.cell_size / 2
            y2 = r2 * self.cell_size + self.cell_size / 2
            line = self.scene.addLine(x1, y1, x2, y2, pen)

    def get_cell_from_pos(self, pos):
        """Convert scene position to grid cell coordinates."""
        x, y = pos.x(), pos.y()
        c = int(x // self.cell_size)
        r = int(y // self.cell_size)
        if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
            return (r, c)
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.grid:
            # Emit signal that puzzle was clicked (to clear hints)
            self.puzzle_clicked.emit()
            
            cell = self.get_cell_from_pos(self.mapToScene(event.pos()))
            if cell:
                self.is_dragging = True
                self.drag_start_cell = cell
                self.drag_current_cell = cell
                self.current_temp_path = [cell]
                self.redraw()

    def mouseMoveEvent(self, event):
        if self.is_dragging and self.grid:
            cell = self.get_cell_from_pos(self.mapToScene(event.pos()))
            if cell and cell != self.drag_current_cell:
                # Check if this forms a valid line with the start
                if self.is_valid_drag_path(self.drag_start_cell, cell):
                    self.drag_current_cell = cell
                    self.current_temp_path = self.get_path_between(self.drag_start_cell, cell)
                    self.redraw()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_dragging:
            self.is_dragging = False
            if self.current_temp_path:
                self.word_selected.emit(self.current_temp_path)
            self.current_temp_path = []
            self.redraw()

    def is_valid_drag_path(self, start, end):
        """Check if the drag forms a straight line (horizontal, vertical, or diagonal)."""
        r1, c1 = start
        r2, c2 = end

        dr = r2 - r1
        dc = c2 - c1

        # Must be same row, column, or diagonal
        return dr == 0 or dc == 0 or abs(dr) == abs(dc)

    def get_path_between(self, start, end):
        """Get all cells in a straight line between start and end."""
        r1, c1 = start
        r2, c2 = end

        dr = r2 - r1
        dc = c2 - c1

        # Normalize direction
        steps = max(abs(dr), abs(dc))
        if steps == 0:
            return [start]

        dr_step = dr // steps if dr != 0 else 0
        dc_step = dc // steps if dc != 0 else 0

        path = []
        for i in range(steps + 1):
            r = r1 + dr_step * i
            c = c1 + dc_step * i
            if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
                path.append((r, c))

        return path
