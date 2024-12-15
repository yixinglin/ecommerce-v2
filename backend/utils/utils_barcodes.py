# import barcode as bc
from barcode import Code128
from barcode.writer import SVGWriter
from reportlab.lib.pagesizes import inch
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from reportlab.pdfgen import canvas
from textwrap import wrap
from io import BytesIO
import base64
from core.config import FONT

def generate_barcode_fnsku(fnsku, sku, title, note):
    # Generate the barcode as SVG in memory
    options = {
        "module_height": 16,
        "module_width": 0.43,
        "font_size": 8,
        "text_distance": 2.8,
    }
    barcode = Code128(fnsku, writer=SVGWriter())
    barcode_svg = BytesIO()
    barcode.write(barcode_svg, options=options)

    # PDF Dimensions
    height, width = (1.58 * inch, 3.16 * inch)  # PDF dimensions (Amazon)
    # Create the PDF in memory
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(width, height))

    # Convert SVG bytes to a drawing
    barcode_svg.seek(0)  # Reset the pointer to the beginning of the BytesIO buffer
    drawing = svg2rlg(barcode_svg)  # Convert SVG to ReportLab drawing
    renderPDF.draw(drawing, c, 20, 35)  # Position at (x=20, y=40)

    # Add SKU and Title text
    text_x = 20
    text_y = 32
    font_size = 7
    font = FONT
    c.setFont(font, font_size)
    c.drawString(text_x, text_y, f"SKU: {sku}")
    c.drawString(text_x, 100, note)

    # Wrap the title to fit within max_width
    max_width = 250  # Limit the title width in points (1 inch ≈ 72 points)
    wrapped_title = wrap(title, width=max_width // (font_size * 0.6))  # Approx width of each character
    line_height = font_size + 2  # Adjust line height for spacing
    # Draw each line of the wrapped title
    for i, line in enumerate(wrapped_title):
        c.drawString(text_x, text_y - 10 - (i * line_height), line)

    # Save the PDF to the buffer
    c.save()
    pdf_buffer.seek(0)  # Reset the buffer pointer to the beginning

    # Encode the PDF buffer to Base64
    pdf_base64 = base64.b64encode(pdf_buffer.read()).decode('utf-8')

    return pdf_base64

import datetime

if __name__ == '__main__':
    # 示例使用
    fnsku = "X0026ICM3F"
    sku = "77380773807738077380"
    title = """新New - Pflasteräüß Rolle 6cm x 5m, Elastischer Wundverband, Pflaster Box Wundpflaster Heftpflaster, hypoallergen, atmungsaktiv, Weiß Starke Klebekraft (6cm x 5m)"""
    index = 1
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    text = f"[{index:03d}] {date}"
    b64 = generate_barcode_fnsku(fnsku, sku, title, text)
    print(b64)
    with open("barcode.pdf", "wb") as f:
        f.write(base64.b64decode(b64))