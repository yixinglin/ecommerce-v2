from datetime import datetime, timedelta

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

def  days_ago(days: int) -> str:
    """
    Get the date that is `days` days ago.
    :param days:
    :return:
    """
    return (datetime.now() - timedelta(days=days)).strftime(DATETIME_PATTERN)

def str_to_datatime(datetime_str, pattern=DATETIME_PATTERN):
    """
    Convert a string to datetime object.
    :param date_str:
    :param pattern:
    :return:
    """
    return datetime.strptime(datetime_str, pattern)

def datetime_to_str(datetime_obj, pattern=DATETIME_PATTERN):
    """
    Convert a datetime object to string.
    :param datetime_obj:
    :param pattern:
    :return:
    """
    return datetime_obj.strftime(pattern)

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

def datetime_to_date(datetime_str, src_pattern=DATETIME_PATTERN,
                     target_pattern='%Y-%m-%d') -> str:
    """
    Convert a datetime string to date object.
    :param datetime_str:
    :param pattern:
    :return:
    """
    return datetime.strptime(datetime_str, src_pattern).strftime(target_pattern)
