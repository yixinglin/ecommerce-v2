import jsonpath as jp_

def isEmpty(string):
    return string is None or string.strip() == ""

def jsonpath(obj: dict, expr: str):
    return jp_.jsonpath(obj, expr)
