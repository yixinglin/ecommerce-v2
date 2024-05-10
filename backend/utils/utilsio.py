import csv
from io import StringIO
from typing import List


def convert_list_to_csv_string(data: List[List[str]]):
    # Convert data to CSV string
    output = StringIO()
    csv_writer = csv.writer(output, delimiter=';')
    csv_writer.writerows(data)
    return output.getvalue()

