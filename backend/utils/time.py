from datetime import datetime

DATETIME_PATTERN = '%Y-%m-%dT%H:%M:%SZ'

def now(pattern=DATETIME_PATTERN):
    """
    Get the current time. Default format is ISO-8601.
    :return:
    """
    return datetime.now().strftime(pattern)


def today():
    """
    Get the current date.
    :return:
    """
    return datetime.now().date()

def str_to_datatime(datetime_str, pattern=DATETIME_PATTERN):
    """
    Convert a string to datetime object.
    :param date_str:
    :param pattern:
    :return:
    """
    return datetime.strptime(datetime_str, pattern)

def diff_datetime(datetime_str1, datetime_str2, pattern=DATETIME_PATTERN):
    """
    Calculate the difference between two datetime strings.
    :param datetime_str1: Datetime string 1.
    :param datetime_str2: Datetime string 2.
    :param pattern: Datetime pattern.
    :return: The difference in seconds.
    """
    dt1 = str_to_datatime(datetime_str1, pattern)
    dt2 = str_to_datatime(datetime_str2, pattern)
    return (dt1 - dt2).total_seconds()
