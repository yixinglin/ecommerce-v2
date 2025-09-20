import base64
import io
from typing import List, Union, Tuple, Optional

import PyPDF2
from PyPDF2.errors import PdfReadError
from PyPDF2.generic import RectangleObject
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

def extract_pdf_size(file: Union[bytes, str]) -> Tuple[float, float]:
    if isinstance(file, str):
        pdf_reader = PyPDF2.PdfReader(file)
    elif isinstance(file, bytes):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file))
    else:
        raise TypeError("File must be a string or bytes object.")
    return (float(pdf_reader.pages[0].mediabox.width),
            float(pdf_reader.pages[0].mediabox.height))


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

def count_pages(file: Union[bytes, str]) -> int:
    """
    Counts the number of pages in a PDF file.
    :param pdf_bytes:  The PDF file as bytes.
    :return:  The number of pages in the PDF file.
    """
    if isinstance(file, str):
        pdf_reader = PyPDF2.PdfReader(file)
    elif isinstance(file, bytes):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file))
    else:
        raise TypeError("File must be a string or bytes object.")
    return len(pdf_reader.pages)

def is_pdf(file: Union[bytes, str]):
    if isinstance(file, str):
        try:
            PyPDF2.PdfReader(file)
            return True
        except PdfReadError:
            return False
    elif isinstance(file, bytes):
        try:
            PyPDF2.PdfReader(io.BytesIO(file))
            return True
        except PdfReadError:
            return False
    else:
        raise TypeError("File must be a string or bytes object.")

def extract_pdf_pages(file: Union[bytes, str], page_list: List[int],
                      extra_info: str = None):
    """
    Extracts a range of pages from a PDF file.
    :param pdf_bytes:  The PDF file as bytes.
    :param page_list:  A list of page numbers (from 1).
    :return:  The extracted PDF file as bytes.
    """
    if isinstance(file, str):
        pdf_reader = PyPDF2.PdfReader(file)
    elif isinstance(file, bytes):
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file))
    else:
        raise TypeError("File must be a string or bytes object.")

    pdf_writer = PyPDF2.PdfWriter()
    for i in page_list:
        if 1 <= i <= len(pdf_reader.pages):
            pdf_writer.add_page(pdf_reader.pages[i - 1])
        else:
            break

    page_size = (pdf_reader.pages[0].mediabox.height, pdf_reader.pages[0].mediabox.width)
    if extra_info:
        watermark_pdf_bytes = create_watermark_text(watermark_text=extra_info,
                                                    position=(20, 20),
                                                    page_size=page_size)
        watermark_pdf_reader = PyPDF2.PdfReader(io.BytesIO(watermark_pdf_bytes))
        watermark_page = watermark_pdf_reader.pages[0]
        # Append watermark to the last page
        pdf_writer.add_page(watermark_page)
    buffer = io.BytesIO()
    pdf_writer.write(buffer)
    return buffer.getvalue()

def mm(*args):
    """
    Converts millimeters to points.
    :param args:
    :return:
    """
    return tuple(int(v * 2.835) for v in args)

def crop_pdf_area(
    file: Union[bytes, str],
    crop_box: Tuple[float, float, float, float],
) -> bytes:
    """
    Crops a rectangular area from a PDF file.
    :param file:  The PDF file as bytes or a file path.
    :param crop_box:  The crop box as a tuple of (x0, y0, x1, y1) in pt.
    :return:  The cropped PDF file as bytes.
    """
    if isinstance(file, str):
        reader = PyPDF2.PdfReader(file)
    elif isinstance(file, bytes):
        reader = PyPDF2.PdfReader(io.BytesIO(file))
    else:
        raise TypeError("File must be a string or bytes object.")

    writer = PyPDF2.PdfWriter()

    for page in reader.pages:
        # 应用裁剪框
        page.cropbox = RectangleObject(crop_box)
        writer.add_page(page)

    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    return output_buffer.getvalue()


def add_page_numbers(input_bytes: bytes,
                     font_size: int = 6,
                     position: Tuple[float, float] = (5, 5),
                     page_list: Optional[List[int]] = None
                     ) -> bytes:
    input_pdf = io.BytesIO(input_bytes)
    reader = PyPDF2.PdfReader(input_pdf)
    writer = PyPDF2.PdfWriter()
    total_pages = len(reader.pages)
    if isinstance(page_list, (list, tuple)) and len(page_list) != total_pages:
        raise ValueError('The length of page_list must be equal to the total number of pages in the PDF file.')

    for i in range(total_pages):
        original_page = reader.pages[i]
        width = float(original_page.mediabox.width)
        height = float(original_page.mediabox.height)

        # 创建与原页面相同尺寸的PDF页，写上页码
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))

        if page_list:
            page_num_text = f"{page_list[i]}"
        else:
            page_num_text = f"{i + 1} / {total_pages}"
        textObj = can.beginText(*position)
        textObj.setFont("Helvetica", font_size)
        textObj.textLine(page_num_text)
        can.drawText(textObj)
        can.save()
        packet.seek(0)

        overlay_pdf = PyPDF2.PdfReader(packet)
        overlay_page = overlay_pdf.pages[0]

        original_page.merge_page(overlay_page)
        writer.add_page(original_page)

    output_stream = io.BytesIO()
    writer.write(output_stream)
    return output_stream.getvalue()


def demo1():
    with open(r'G:\hansagt\ecommerce\backend\.temp\T-Code透明码4.16-Drucken\TCodes_PID4890922130103254976_FBA-HMMD-25070_04260715494105_202504211801.pdf', 'rb') as f:
        pdf_bytes = f.read()
        count = count_pages(pdf_bytes)
        print(count)


    # text = extract_datamatrix_from_pdf(pdf_bytes)
    # print(text)

    # extracted_pdf_bytes = extract_pdf_pages(pdf_bytes, 1, 2201)
    extra_info = "This is an 55你哈 extröa info\nThis is an extra info\nThis is an extra info"
    page_list = list(range(1, 1900, 2))
    print(page_list)
    extracted_pdf_bytes = extract_pdf_pages(pdf_bytes, page_list, extra_info)

    # crop_box = mm(0, 0, 35, 35)
    crop_box = mm(0, 0, 38, 38)
    # extracted_pdf_bytes = crop_pdf_area(extracted_pdf_bytes, crop_box)
    # extracted_pdf_bytes = add_page_numbers(extracted_pdf_bytes,
    #                                        position=mm(15.0, 2.0),
    #                                        page_list=page_list + [-1])

    with open("extracted.pdf", "wb") as f:
        f.write(extracted_pdf_bytes)

def demo2():
    # FN Code
    with open(r'G:\hansagt\ecommerce\backend\.temp\01230.pdf', 'rb') as f:
        pdf_bytes = f.read()

    w, h = extract_pdf_size(pdf_bytes)
    print(w, h)

    total_pages = 700
    page_list = list(range(1, total_pages+1))
    print(f"Total pages: {total_pages}")
    pdf_list = [pdf_bytes] * total_pages
    merged_pdf_bytes = concat_pdfs(pdf_list)
    print(f"Merged PDF size: {len(merged_pdf_bytes)} bytes")
    pdf_with_page_numbers = add_page_numbers(
        merged_pdf_bytes,
        page_list=None,
        position=(w / 2 + 50, h - 10),
    )
    print(f"PDF with page numbers size: {len(pdf_with_page_numbers)} bytes")
    with open("merged.pdf", "wb") as f:
        f.write(pdf_with_page_numbers)


if __name__ == '__main__':
    demo2()