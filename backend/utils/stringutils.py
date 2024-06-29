from collections import OrderedDict, Counter

import jsonpath as jp_

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

def remove_duplicates(lst: list):
    """
    Removes duplicates from a list while preserving the order of the elements.
    :param lst:  The list to remove duplicates from.
    :return:  The list with duplicates removed.
    """
    return list(OrderedDict.fromkeys(lst))

def count_elements(lst):
    return dict(Counter(lst))