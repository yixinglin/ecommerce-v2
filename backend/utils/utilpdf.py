import base64
import io
from typing import List

import PyPDF2
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas

PARCEL_LABEL = (4.126 * inch, 5.835 * inch)
GLS_TEXT_POS = (8 * mm, 65 * mm)

def str_to_pdf(base64_pdf_string: str) -> bytes:
    """
    Converts a base64 encoded PDF string to a bytes object.
    :param base64_pdf_string:  The base64 encoded PDF string.
    :return:  The PDF file as bytes.
    """
    pdf_bytes = base64.b64decode(base64_pdf_string)
    return pdf_bytes

def pdf_to_str(pdf: bytes) -> str:
    """
    Converts a PDF file to a base64 encoded string.
    :param pdf:  The PDF file as bytes.
    :return:  The base64 encoded PDF string.
    """
    base64_pdf_string = base64.b64encode(pdf).decode('utf-8')
    return base64_pdf_string


def create_watermark_text(watermark_text: str,
                          font_size: int = 8,
                          position: tuple = (100, 100),
                          font_color: tuple = (0, 0, 0),
                          page_size: tuple = PARCEL_LABEL) -> bytes:
    """
    Creates a watermark text as a PDF file.
    :param page_size:
    :param watermark_text:  The watermark text to create.
    :param font_size:  The font size of the watermark text.
    :param font_color:  The font color of the watermark text.
    :param position:  The position of the watermark text on the page.
    :return:  The watermark text as a PDF file as bytes.
    """
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=page_size, bottomup=0)
    can.setFont("Helvetica", font_size)
    can.setFillColorRGB(*font_color)
    x, y = position
    textObj = can.beginText(x, y)
    textObj.setFont("Helvetica", font_size)
    for line in watermark_text.split('\n'):
        textObj.textLine(line.strip())
    can.drawText(textObj)
    can.save()
    packet.seek(0)
    return packet.read()


def concat_pdfs(pdf_bytes_list: List[bytes]) -> bytes:
    """
    Concatenates multiple PDF files into one PDF file.
    :param pdf_bytes_list:  A list of PDF files as bytes.
    :return:  The merged PDF file as bytes.
    """
    pdf_writer = PyPDF2.PdfWriter()
    for pdf_bytes in pdf_bytes_list:
        with io.BytesIO(pdf_bytes) as fp:
            pdf_reader = PyPDF2.PdfReader(fp)
            for page_num in range(len(pdf_reader.pages)):
                pdf_writer.add_page(pdf_reader.pages[page_num])
    concat_pdf_bytes = io.BytesIO()
    pdf_writer.write(concat_pdf_bytes)
    return concat_pdf_bytes.getvalue()


def add_watermark(pdf_bytes: bytes,
                  watermark_text: str,
                  **kwargs) -> bytes:
    """
    Adds a watermark to a PDF file.
    :param pdf_bytes:  The PDF file as bytes.
    :param watermark_text:  The watermark text to add to the PDF file.
    :return:  The PDF file with the watermark added as bytes.
    """
    watermark_pdf_bytes = create_watermark_text(watermark_text=watermark_text, **kwargs)
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    watermark_pdf_reader = PyPDF2.PdfReader(io.BytesIO(watermark_pdf_bytes))
    pdf_writer = PyPDF2.PdfWriter()
    watermark_page = watermark_pdf_reader.pages[0]
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        page.merge_page(watermark_page)
        pdf_writer.add_page(page)
    watermarked_pdf_bytes = io.BytesIO()
    pdf_writer.write(watermarked_pdf_bytes)
    return watermarked_pdf_bytes.getvalue()

# def html_to_pdf(html_string: str,) -> bytes:
#     """
#     Converts an HTML string to a PDF file.
#     :param html_string:  The HTML string to convert.
#     :return:  The PDF file as bytes.
#     """
#     # pdf_bytes = weasyprint.HTML(string=html_string).write_pdf()
#     pdfkit.from_string(html_string, 'output.pdf')
#     return None


# import asyncio
# from pyppeteer import launch
# async def html_to_pdf(html_content):
#     browser = await launch()
#     page = await browser.newPage()
#     await page.setContent(html_content)
#     await page.pdf({'path': "output.pdf"})
#     await browser.close()