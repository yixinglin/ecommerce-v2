import json
import re
from typing import Tuple

import pycountry

PTH_COUNTRIES_JSON = "assets/static/countries.json"


def country_name_to_alpha2(country_name):
    """
    :param country_name:
    :return: [  "Österreich": {
                "short_name": "Austria",
                "alpha_2": "AT",
                "alpha_3": "AUT"
            }]
    """
    try:
        country = pycountry.countries.lookup(country_name)
        alpha_2 = country.alpha_2
    except LookupError:
        # if country is not found
        alpha_2 = None
    return alpha_2


def country_name_details(native_name="Deutschland"):
    with open(PTH_COUNTRIES_JSON, encoding="utf-8") as f:
        countries = json.load(f)
    return countries[native_name]


def country_name_details_by_shortname(shortname):
    with open(PTH_COUNTRIES_JSON, encoding="utf-8") as f:
        countries = json.load(f)
    c = list(filter(lambda x: x['short_name'].upper() == shortname.upper(), list(countries.values())))
    if len(c) == 0:
        return None
    return c[0]


def valid_zip_code(zipcode, countryCode='DE') -> bool:
    """
    Check if zip code valid
    :param zipcode:
    :param countryCode:
    :return:
    """
    with open(PTH_COUNTRIES_JSON, encoding="utf-8") as f:
        countries = json.load(f)
    c = filter(lambda x: x['alpha_2'] == countryCode.upper(), countries.values())
    pattern = list(c)[0]["pattern"]
    return re.fullmatch(pattern, zipcode) is not None

def identify_german_street(address):
    address = address.replace(' - ','-').replace(' / ','/')
    pattern = r"([A-Za-zäöüÄÖÜß])-([A-Za-zäöüÄÖÜß])"   # e.g. "M-Str." to "M_Str."
    address = re.sub(pattern,  r'\1_\2', address)
    pattern = r"([\d]+)\s([A-Za-z])"   # e.g. "2 A"  to "2A"
    address = re.sub(pattern, r'\1\2', address)

    pattern = r'^([A-Za-zäöüÄÖÜß][A-Za-zäöüÄÖÜß\s\._]*)\s*((?:\d{1,3}[a-zA-Z]?(?:[-/\s]\d{1,3}[a-zA-Z]?)+|\d{1,3}[a-zA-Z]?))$'
    # 匹配地址
    match = re.match(pattern, address)
    if match:
        street_name = match.group(1).strip()
        house_number = match.group(2).strip()
        return (street_name, house_number)
    else:
        return None


def is_company_name(company_name: str) -> bool:
    keywords = r'\b(GmbH|Gmbh|gGmbH|AG|KG|OHG|UG|e\.V\.|SE)\b'
    match = re.search(keywords, company_name)
    return bool(match)

# Test patterns
postcodes = {
    "DE": ["12345", "1234", "123456"],
    "FR": ["12345", "1234", "123456"],
    "IT": ["12345", "1234", "123456"],
    "ES": ["12345", "1234", "123456"],
    "NL": ["1234AB", "1234", "1234ABCD"],
    "BE": ["1234", "123456"],
    "AT": ["1234", "123456"],
    "SE": ["123 45", "12345", "1234"],
    "DK": ["1234", "123456"],
    "FI": ["12345", "1234", "123456"],
    "PT": ["1234-123", "12345", "1234-12345"],
    "GR": ["123 45", "12345", "1234"],
    "IE": ["A12 BC34", "123 45", "12345"],
    "HU": ["1234", "123456"],
    "PL": ["12-345", "12345", "12-3456"],
    "CZ": ["123 45", "12345", "1234"],
    "SK": ["123 45", "12345", "1234"],
    "HR": ["12345", "1234", "123456"],
    "LT": ["LT-12345", "LT-123456"],
    "LV": ["LV-1234", "LV-123456"],
    "EE": ["12345", "1234", "123456"],
    "SI": ["SI-1234", "SI-123456"],
    "CY": ["1234", "12345", "123456"],
    "MT": ["ABC 123", "ABC 1234", "ABC 12345", "ABC 123456"],
    "LU": ["1234", "123456"],
    "BG": ["1234", "12345", "123456"],
    "RO": ["123456", "1234567"],
    "GB": ["W1A 1AA", "W1 6ZB", "EC1A 1BB", "B33 8TH", "CR2 6XH", "DN55 1PT", "GIR 0AA"],
    "TR": ["12345", "1234", "123456"]
}



if __name__ == '__main__':
    alpha2 = country_name_details("Deutschland")
    print(alpha2)
    # Validate postcodes
    # for countryCode, codes in postcodes.items():
    #     for code in codes:
    #         if valid_zip_code(code, countryCode):
    #             print(f"{code} is a valid {countryCode} zip code")
    #         else:
    #             print(f"{code} is an invalid {countryCode} zip code")


