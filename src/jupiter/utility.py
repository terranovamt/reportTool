def read_csv_with_fallback(path):
    import pandas as pd
    from pandas.errors import EmptyDataError, ParserError
    import os

    try:
        # print (os.path.abspath(path))
        return pd.read_csv(os.path.abspath(path))
    except (EmptyDataError, FileNotFoundError, ParserError) as e:
        # print("ERROR:", e)
        return pd.DataFrame()


# Customize cell colors
def color_cpk(val):
    try:
        val = float(val)
    except ValueError:
        return ""
    if isinstance(val, (int, float)):
        if val < 1.2:
            return "background-color: #F23202"
        elif 1.2 <= val < 1.3:
            return "background-color: #E85D04"
        elif 1.3 <= val < 1.4:
            return "background-color: #F48C06"
        elif 1.4 <= val < 1.5:
            return "background-color: #FAA307F0"
        elif 1.5 <= val <= 1.6:
            return "background-color: #FFBA08F1"
        else:
            return ""
    return ""

def color_kurtosis(val):
    try:
        val = float(val)
    except ValueError:
        return ""
    if isinstance(val, (int, float)):
        if val > -0.2:
            return "background-color: #F23202"
        elif -0.2 >= val > -0.4:
            return "background-color: #E85D04"
        elif -0.4 >= val > -0.6:
            return "background-color: #F48C06"
        elif -0.6 >= val > -0.8:
            return "background-color: #FAA307F0"
        elif -0.8 >= val >= -1.0:
            return "background-color: #FFBA08F1"
        else:
            return ""
    return ""


# Customize cell colors
def color_cp(val):
    try:
        val = float(val)
    except ValueError:
        return ""
    if isinstance(val, (int, float)):
        if val < 6:
            return "background-color: #F23202"
        elif 6 <= val < 7:
            return "background-color: #E85D04"
        elif 7 <= val < 8:
            return "background-color: #F48C06"
        elif 8 <= val < 9:
            return "background-color: #FAA307F0"
        elif 9 <= val <= 10:
            return "background-color: #FFBA08F1"
        else:
            return ""
    return ""


def power_of_10(value):
    if value >= 0:
        return 10**value
    else:
        return 1 / (10 ** abs(value))


def find_value(value, calc_type):
    if value == 0:
        if calc_type == "min":
            min_value = -0.01
            # print(f"Valore attuale: {value} Minimo: {min_value}")
            return 0.01
        elif calc_type == "max":
            max_value = 0.01
            # print(f"Valore attuale: {value} Massimo: {max_value}")
            return -0.01
    elif value < 0:
        if calc_type == "min":
            min_value = value - (value * 0.001)
            # print(f"Valore attuale: {value} Minimo: {min_value}")
            return value - (value * 0.001)
        elif calc_type == "max":
            max_value = value + (value * 0.001)
            # print(f"Valore attuale: {value} Massimo: {max_value}")
            return value + (value * 0.001)
    else:
        if calc_type == "min":
            min_value = value + (value * 0.001)
            # print(f"Valore attuale: {value} Minimo: {min_value}")
            return value + (value * 0.001)
        elif calc_type == "max":
            max_value = value - (value * 0.001)
            # print(f"Valore attuale: {value} Massimo: {max_value}")
            return value - (value * 0.001)


def write_log(message, filename="../run.log"):
    import os
    import datetime

    now = datetime.datetime.now()
    timestamp = now.strftime("[%Y-%m-%d %H:%M:%S]")

    try:
        with open(filename, "r+") as file:
            content = file.readlines()
            # Limit the content to the last 499 lines
            if len(content) >= 500:
                content = content[:499]

            # Calculate time difference if there is a previous log entry
            if content:
                last_timestamp_str = content[0].split("] ")[0].strip("[ ]")
                last_timestamp = datetime.datetime.strptime(last_timestamp_str, "%Y-%m-%d %H:%M:%S")
                time_diff = now - last_timestamp
                diff_str = " (+{})".format(str(time_diff).split(".")[0])
            else:
                diff_str = ""

            # Insert the new log entry at the beginning
            content.insert(0, timestamp + diff_str + " |--> " + message + "\n")
            # Write back the content to the file
            file.seek(0)
            file.writelines(content)
            file.truncate()
    except FileNotFoundError:
        with open(filename, "w") as file:
            file.write(timestamp + " |--> " + message + "\n")
            file.write(timestamp + " Log file created.\n")
    except OSError as e:
        print(f"An error occurred: {e}")
