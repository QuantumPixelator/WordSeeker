"""
Export functions for Word Search Creator.
Handles PNG and PDF export functionality.
"""

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import letter

from constants import PNG_CELL_SIZE, CELL_SIZE


def export_grid_to_png(grid, grid_size, bg_color, fg_color, filename):
    """
    Export the grid to a PNG file.
    
    Args:
        grid: 2D list of letters
        grid_size: Size of the grid
        bg_color: QColor for background
        fg_color: QColor for foreground (text)
        filename: Output filename path
    """
    img_width = grid_size * PNG_CELL_SIZE
    img_height = grid_size * PNG_CELL_SIZE

    # Convert QColor to hex string with '#' for PIL
    bg_color_hex = bg_color.name()  # Keep the # for PIL
    fg_color_hex = fg_color.name()  # Keep the # for PIL
    
    img = Image.new('RGB', (img_width, img_height), bg_color_hex)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", PNG_CELL_SIZE - 10)
    except:
        font = ImageFont.load_default()

    # Draw grid
    for r in range(grid_size):
        for c in range(grid_size):
            x = c * PNG_CELL_SIZE
            y = r * PNG_CELL_SIZE

            # Draw cell background
            draw.rectangle([x, y, x + PNG_CELL_SIZE, y + PNG_CELL_SIZE],
                         fill=bg_color_hex,
                         outline='#cccccc')

            # Draw letter
            letter = grid[r][c]
            if letter != ' ':
                bbox = draw.textbbox((0, 0), letter, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = x + (PNG_CELL_SIZE - text_width) // 2
                text_y = y + (PNG_CELL_SIZE - text_height) // 2
                draw.text((text_x, text_y), letter, fill=fg_color_hex, font=font)

    img.save(filename)


def export_grid_to_pdf(grid, grid_size, words, filename):
    """
    Export the grid to a PDF file.
    
    Args:
        grid: 2D list of letters
        grid_size: Size of the grid
        words: Set of words to include in the word list
        filename: Output filename path
    """
    pdf = pdf_canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Calculate scaling to fit on page
    grid_pixel_width = grid_size * CELL_SIZE
    grid_pixel_height = grid_size * CELL_SIZE

    scale_x = (width * 0.8) / grid_pixel_width
    scale_y = (height * 0.8) / grid_pixel_height
    scale = min(scale_x, scale_y, 1.0)

    # Center the grid
    offset_x = (width - grid_pixel_width * scale) / 2
    offset_y = (height - grid_pixel_height * scale) / 2

    pdf.translate(offset_x, offset_y)
    pdf.scale(scale, scale)

    # Draw grid
    for r in range(grid_size):
        for col in range(grid_size):
            x = col * CELL_SIZE
            y = height - offset_y * 2 - (r + 1) * CELL_SIZE  # Flip Y coordinate for PDF

            # Draw cell
            pdf.rect(x, y, CELL_SIZE, CELL_SIZE, stroke=1, fill=0)

            # Draw letter
            letter_char = grid[r][col]
            if letter_char != ' ':
                pdf.setFont("Helvetica-Bold", CELL_SIZE * 0.6)
                pdf.drawString(x + CELL_SIZE * 0.2, y + CELL_SIZE * 0.2, letter_char)

    # Add words list below the grid
    pdf.scale(1/scale, 1/scale)  # Reset scale
    pdf.translate(-offset_x, -offset_y)  # Reset translation

    words_y = offset_y - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(offset_x, words_y, "Words to Find:")
    words_y -= 20

    pdf.setFont("Helvetica", 12)
    sorted_words = sorted(words)
    for i, word in enumerate(sorted_words):
        if i % 10 == 0 and i > 0:
            words_y -= 20  # New line every 10 words
        pdf.drawString(offset_x + (i % 10) * 80, words_y, word)

    pdf.save()
