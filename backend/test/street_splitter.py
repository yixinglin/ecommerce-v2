import re


def identify_german_street(address):
    # Preprocess the address
    address = address.replace(' - ','-').replace(' / ','/')
    pattern = r"([A-Za-zäöüÄÖÜß])-([A-Za-zäöüÄÖÜß])"   # e.g. "M-Str." to "M_Str."
    address = re.sub(pattern,  r'\1_\2', address)
    pattern = r"([\d]+)\s([A-Za-z])"   # e.g. "2 A"  to "2A"
    address = re.sub(pattern, r'\1\2', address)
    # 定义正则表达式模式
    # pattern = r'^([A-Za-zäöüÄÖÜß][A-Za-zäöüÄÖÜß\s\._]*)\s*((?:\d{1,3}[a-zA-Z]?(?:[-/]\d{1,3}[a-zA-Z]?)+|\d{1,3}[a-zA-Z]?))$'
    pattern = r'^([A-Za-zäöüÄÖÜß][A-Za-zäöüÄÖÜß\s\._]*)\s*((?:\d{1,3}[a-zA-Z]?(?:[-/\s]\d{1,3}[a-zA-Z]?)+|\d{1,3}[a-zA-Z]?))$'

    # 匹配地址
    match = re.match(pattern, address)
    if match:
        street_name = match.group(1).strip()
        house_number = match.group(2).strip()
        return (street_name, house_number)
    else:
        return None


# 单元测试
def test_identify_german_street():
    # 测试用例
    test_cases = [
        ('Schlossstraße 123', ('Schlossstraße', '123')),
        ('Bahnstraße 2a', ('Bahnstraße', '2a')),
        ('Am Hauptbahnhof 7-9', ('Am Hauptbahnhof', '7-9')),
        ('Hauptplatz 15/17/19', ('Hauptplatz', '15/17/19')),
        ('Hauptplatz 15a/17a/19a', ('Hauptplatz', '15a/17a/19a')),
        ('Invalid Address E', None),
        ('Straße 1-3', ('Straße', '1-3')),  # 包含连字符
        ('Straße 1/3', ('Straße', '1/3')),  # 包含斜杠
        ('Münster Str. 1/3', ('Münster Str.', '1/3')),
        ('Münster Str. 1a/3a', ('Münster Str.', '1a/3a')),
        ('Münster-Str. 1a/3a', ('Münster_Str.', '1a/3a')),
        ('Straße 123a', ('Straße', '123a')),  # 含字母
        ('Straße 123', ('Straße', '123')),  # 不含字母
        ('Straße 123 - 123', ('Straße', '123-123')),
        ('Muster Straße 123 - 123', ('Muster Straße', '123-123')),
        ('Herrenmühle 14 B', ('Herrenmühle', '14B')),
        ('Herrenmühle 14 15', ('Herrenmühle', '14 15')),
        ('Bahnstraße2', ('Bahnstraße', '2')),
        ('Bahnstraße2a', ('Bahnstraße', '2a')),
        # ('Muster Straße 123  - 123', ('Muster Straße', '123-123')),
        ('123', None),  # 无街名
        ('Straße', None),  # 无房号
        ('-Straße 123', None),  # 街名不合法
        ('Straße -123', None),  # 房号不合法
    ]

    # 遍历测试用例
    for address, expected_result in test_cases:
        result = identify_german_street(address)
        assert result == expected_result, f"Test case failed: {address}, Expected: {expected_result}, Got: {result}"

    print("All test cases passed!")


# 运行单元测试
test_identify_german_street()
