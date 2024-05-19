from datetime import datetime


def print_array_in_format(arr, num_columns=4):
    string = ""
    for i in range(0, len(arr), num_columns):
        for j in range(num_columns):
            if i + j < len(arr):
                # print(f"{arr[i + j]:<30}", end=" ")
                string += f"{arr[i + j]:<30}"
        string += "\n"
    string += f"Size: {len(arr)}\n"
    return string


def today(format="%Y-%m-%d %H:%M:%S"):
    return datetime.now().strftime(format)

