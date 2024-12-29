def read_csv_with_fallback(path):
    import pandas as pd
    from pandas.errors import EmptyDataError, ParserError
    import os

    try:
        print (os.path.abspath(path))
        return pd.read_csv(os.path.abspath(path))
    except (EmptyDataError, FileNotFoundError, ParserError) as e:
        print("ERROR:", e)
        return pd.DataFrame()


# Customize cell colors
def color_cpk(val):
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


# Customize cell colors
def color_cp(val):
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
            min_value = -0.1
            # print(f"Valore attuale: {value} Minimo: {min_value}")
            return 0.1
        elif calc_type == "max":
            max_value = 0.1
            # print(f"Valore attuale: {value} Massimo: {max_value}")
            return -0.1
    elif value < 0:
        if calc_type == "min":
            min_value = value - (value * 0.1)
            # print(f"Valore attuale: {value} Minimo: {min_value}")
            return value - (value * 0.1)
        elif calc_type == "max":
            max_value = value + (value * 0.1)
            # print(f"Valore attuale: {value} Massimo: {max_value}")
            return value + (value * 0.1)
    else:
        if calc_type == "min":
            min_value = value + (value * 0.1)
            # print(f"Valore attuale: {value} Minimo: {min_value}")
            return value + (value * 0.1)
        elif calc_type == "max":
            max_value = value - (value * 0.1)
            # print(f"Valore attuale: {value} Massimo: {max_value}")
            return value - (value * 0.1)


def write_log(message, filename = "../run.log"):
    import os
    import datetime

    last_timestamp = datetime.datetime.now()
    # filename = os.path.abspath("src/run.log")
    # print(filename)
    now = datetime.datetime.now()
    timestamp = now.strftime("[%Y-%m-%d %H:%M:%S]")
    diff = ""
    if last_timestamp is not None:
        time_diff = now - last_timestamp
        diff = " (+{}) |--> ".format(str(time_diff).split(".")[0])
    try:
        with open(filename, "r+") as file:
            content = file.read()
            file.seek(0, 0)
            file.write(
                timestamp + 
                # diff + 
                " |--> " +
                message + 
                "\n" + 
                content
            )
    except FileNotFoundError:
        with open(filename, "w") as file:
            file.write(timestamp + diff + message + "\n")
            file.write(timestamp + " Log file created.\n")
    except OSError as e:
        print(f"An error occurred: {e}")
