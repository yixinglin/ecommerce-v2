import base64
import hashlib
from collections import OrderedDict, Counter
from typing import List
import re

import jsonpath as jp_
import barcode
from barcode.writer import SVGWriter


def isEmpty(string):
    return string is None or string.strip() == ""

def jsonpath(obj: dict, expr: str, default=None):
    data = jp_.jsonpath(obj, expr)
    if data is None:
        return default

    if isinstance(data, list) and len(data) == 1:
        return data[0]
    else:
        return data

def text_to_md5(text: str) -> str:
    md5_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    return md5_hash


def remove_duplicates(lst: list):
    """
    Removes duplicates from a list while preserving the order of the elements.
    :param lst:  The list to remove duplicates from.
    :return:  The list with duplicates removed.
    """
    return list(OrderedDict.fromkeys(lst))

def count_elements(lst):
    return dict(Counter(lst))

def to_german_price(price: float):
    return "{:.2f} €".format(price)

def generate_barcode_svg(code: str) -> str:
    """
    Generates a barcode SVG image from a code.
    :param code:  The code to generate the barcode for.
    :return:  The SVG image as a base64 string.
    """
    EAN = barcode.get_barcode_class('code128')
    # 设置条形码高度为1厘米，字体大小是8px
    barcode_svg = EAN(code, writer=SVGWriter())
    # barcode_svg = EAN(code, writer=SVGWriter())
    svg_string: str = barcode_svg.render(writer_options={'height': 10, 'font_size': 8})
    svg_string = svg_string.decode('utf-8')
    # to base64
    svg_string = "data:image/svg+xml;base64," + str(base64.b64encode(svg_string.encode('utf-8')), 'utf-8')
    return svg_string


def base64_encode_str(text: str) -> str:
    """
    Encodes a string to base64.
    :param text:  The text to encode.
    :return:  The base64 encoded string.
    """
    return str(base64.b64encode(text.encode('utf-8')), 'utf-8')

def base64_decode_str(base64_str: str) -> str:
    """
    Decodes a base64 string.
    :param base64_str:  The base64 string to decode.
    :return:  The decoded string.
    """
    return str(base64.b64decode(base64_str.encode('utf-8')), 'utf-8')


def format_ranges(nums: List[int]):
    """
    Formats a list of numbers into a list of ranges.
    :param nums:  The list of numbers to format.
    :return:  The list of ranges.
    Example:
    >>> format_ranges([1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15])
    ['1-3', '5-8', '10-15']
    """
    if not nums:
        return []

    nums = sorted(set(nums))  # Remove duplicates and sort
    result = []
    start = end = nums[0]

    for n in nums[1:]:
        if n == end + 1:
            end = n
        else:
            if start == end:
                result.append(str(start))
            else:
                result.append(f"{start}-{end}")
            start = end = n

    # Add the last range
    if start == end:
        result.append(str(start))
    else:
        result.append(f"{start}-{end}")

    return result

def split_seller_sku(seller_sku):
    pattern = r"^(.*?)(PK\d+)$"
    match = re.match(pattern, seller_sku)
    if match:
        base = match.group(1)
        n_pack = match.group(2)
        n_pack = int(n_pack.replace("PK", ""))
    else:
        base = seller_sku
        n_pack = 1
    return base, n_pack

from pypinyin import pinyin, lazy_pinyin
def chinese_to_pinyin(text: str, tone: bool = True, separator: str = " ") -> str:
    """
    将中文转换为拼音
    :param chinese:
    :param tone:
    :return:
    """
    if tone:
        pinying_list = pinyin(text)
        pinying_list = ["".join(item) for item in pinying_list]
    else:
        pinying_list = lazy_pinyin(text)
    return separator.join(pinying_list)

