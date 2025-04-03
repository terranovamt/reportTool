import asyncio
import platform

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
import json
import warnings
import datetime
import fileinput
import subprocess
import pandas as pd
import jupiter.utility as uty
from stdf2csv import *
from rework_stdf import rework_stdf
from condition import condition_rework
from guihtml import guihtml

warnings.filterwarnings("ignore", category=RuntimeWarning)

FILENAME = os.path.abspath("src/run.log")


def read_parameters(file_path):
    """
    Read parameters from a CSV file.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        DataFrame: DataFrame containing parameters.
    """
    try:
        parameters = pd.read_csv(file_path, header=0, sep=",")
        parameters = parameters[parameters["RUN"] != 0].reset_index(drop=True)
        parameters.index += 1
        return parameters
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return pd.DataFrame()


def process_all_wafers(parameter, csv_folder):
    """
    Process all wafers and convert STDF files to CSV.

    Args:
        parameter (dict): Parameters containing LOT, WAFER, and TYPE.
        csv_folder (str): Path to the CSV folder.

    Returns:
        list: List of CSV files generated.
    """
    for i in range(1, 25):
        parameter["WAFER"] = i
        debug and print(stdf_folders, csv_folder)
        process_wafer(parameter, csv_folder, i)


def process_multi_wafers(parameter, csv_folder):
    """
    Process all wafers and convert STDF files to CSV.

    Args:
        parameter (dict): Parameters containing LOT, WAFER, and TYPE.
        csv_folder (str): Path to the CSV folder.

    Returns:
        list: List of CSV files generated.
    """
    wafers = parameter["WAFER"].replace(" ", "").split(",")
    for wafer in wafers:
        parameter["WAFER"] = wafer
        debug and print(stdf_folders, csv_folder)
        process_wafer(parameter, csv_folder, wafer)


def process_single_wafer(parameter, csv_folder):
    """
    Process a single wafer and convert STDF file to CSV.

    Args:
        parameter (dict): Parameters containing LOT, WAFER, and TYPE.
        csv_folder (str): Path to the CSV folder.

    Returns:
        list: List of CSV files generated.
    """
    debug and print(stdf_folders, csv_folder)
    process_wafer(parameter, csv_folder, parameter["WAFER"])


def copySTDF(stdf_folder):
    uty.write_log("Download STDF", FILENAME)
    tmp_folder = ".\\src\\tmpstdf"
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)
    for fold in stdf_folder:
        for item in os.listdir(fold):
            s = os.path.join(fold, item)
            if os.path.isfile(s) and s.endswith(".std"):
                d = os.path.join(tmp_folder, item)
                shutil.copy2(s, d)
    return [tmp_folder]


def clearTmpSTDF():
    try:
        tmp_folder = ".\\src\\tmpstdf"
        for root, dirs, files in os.walk(tmp_folder):
            for name in files:
                os.remove(os.path.join(root, name))
    except Exception as e:
        print(f"ERROE:stdf not found {e}")
        return None


def process_wafer(parameter, csv_folder, wafer):
    """
    Process a wafer and convert STDF files to CSV.

    Args:
        parameter (dict): Parameters containing LOT, WAFER, and TYPE.
        csv_folder (str): Path to the CSV folder.
        wafer (str or int): Wafer number or identifier.

    Returns:
        list: List of CSV files generated.
    """
    parameter["WAFER"] = wafer
    stdf_folder = get_stdf_folder(parameter, wafer)
    debug and print(stdf_folder, csv_folder)
    stdf_folder = copySTDF(stdf_folder)
    uty.write_log("Extract Tests", FILENAME)
    csv_files = stdf2csv(stdf_folder, csv_folder, "-t")
    for csv_file in csv_files:
        parameter["TEST_NUM"] = []
        process_composite(parameter, csv_file, stdf_folder, csv_folder)


def get_stdf_folder(parameter, wafer):
    """
    Construct the STDF folder path based on parameters.

    Args:
        parameter (dict): Parameters containing LOT, WAFER, and TYPE.
        wafer (int): Wafer number.

    Returns:
        str: Constructed STDF folder path.
    """
    try:
        stdf_path = parameter["FILE"].get(str(wafer)).get("path")
        if not stdf_path:
            print(f"Error: No path found for wafer {wafer}")
            return None

        resolved_path = os.path.abspath(stdf_path)

        # Check if the directory exists
        if not os.path.isdir(resolved_path):
            print(f"Error: Directory {resolved_path} does not exist")
            return None

        # Check if there is at least one .std or .stdf file in the directory
        files = os.listdir(resolved_path)
        if not any(file.endswith((".std", ".stdf")) for file in files):
            print(f"Error: No .std or .stdf files found in {resolved_path}")
            return None

        return [resolved_path]
    except Exception as e:
        print(f"Error: {e}")
        return None


def process_composite(parameter, csv_file, stdf_folder, csv_folder):
    """
    Process the composite data from a CSV file and execute the report generation.

    Args:
        parameter (dict): Parameters for processing.
        csv_file (str): CSV file name to process.
    """
    try:
        tsr = pd.read_csv(os.path.abspath(f"src/csv/{csv_file}.tsr.csv"))
        debug and print(tsr)
        if str(parameter["COM"]).upper() == "ALL":
            composites = (
                tsr["TEST_NAM"]
                .str.extract(r"(.*_(.*)_.*:.*|.*_(.*)_..$)")[1]
                .dropna()
                .unique()
            )
            composites = composites[composites != ""]

            for composite in composites[1:]:
                parameter["TITLE"] = composite.upper()
                process_single_composite(
                    parameter, tsr, composite, csv_file, stdf_folder, csv_folder
                )
        elif str(parameter["COM"]).upper() == "TTIME":
            process_ttime(
                parameter, tsr, parameter["COM"], csv_file, stdf_folder, csv_folder
            )
        elif str(parameter["COM"]).upper() == "YIELD":
            process_yield(
                parameter, tsr, parameter["COM"], csv_file, stdf_folder, csv_folder
            )
        elif str(parameter["COM"]).upper() == "CONDITION":
            process_condition(
                parameter, tsr, parameter["COM"], csv_file, stdf_folder, csv_folder
            )
        else:
            process_single_composite(
                parameter, tsr, parameter["COM"], csv_file, stdf_folder, csv_folder
            )
    except Exception as e:
        print(f"Error processing composite: {e}")


def process_condition(parameter, composite, stdf_folder):
    """
    Process a FAKE composite for condition report and execute generation.

    Args:
        parameter (dict): Parameters for processing.
        tsr (DataFrame): DataFrame containing test results.
        composite (str): Composite name to process.
        csv_file (str): CSV file name to process.
    """

    uty.write_log(f"Converting ANAFLOW by COM", FILENAME)
    csv_file = condition_rework(parameter, stdf_folder)
    if len(csv_file) == 0:
        print(f"No Extaction good : {composite}")
        uty.write_log(f"No Extaction good : {composite}", FILENAME)
        return
    parameter["COM"] = composite
    parameter["TEST_NUM"] = ""
    parameter["CSV"] = csv_file

    debug and print(parameter)
    exec(parameter)


def process_yield(parameter, tsr, composite, csv_file, stdf_folder, csv_folder):
    """
    Process a FAKE composite for yeald analysis and execute the report generation.

    Args:
        parameter (dict): Parameters for processing.
        tsr (DataFrame): DataFrame containing test results.
        composite (str): Composite name to process.
        csv_file (str): CSV file name to process.
    """

    uty.write_log(f"Converting tests by test list", FILENAME)
    csv_files = stdf2csv(stdf_folder, csv_folder, f"-b")
    if len(csv_files) == 0:
        print(f"No Extaction good : {composite}")
        uty.write_log(f"No Extaction good : {composite}", FILENAME)
        return
    parameter["COM"] = composite
    parameter["TEST_NUM"] = ""
    parameter["CSV"] = csv_file

    debug and print(parameter)
    exec(parameter)


def process_ttime(parameter, tsr, composite, csv_file, stdf_folder, csv_folder):
    """
    Process a FAKE composite for test time analysis and execute the report generation.

    Args:
        parameter (dict): Parameters for processing.
        tsr (DataFrame): DataFrame containing test results.
        composite (str): Composite name to process.
        csv_file (str): CSV file name to process.
    """
    match_group = tsr["TEST_NAM"].str.extract(r"(log_ttime.*)".format(composite))
    tsr["match_group"] = match_group[0]

    test_numbers = tsr.loc[tsr["match_group"].notnull(), "TEST_NUM"].unique().tolist()

    if "EWS" not in str(parameter["FLOW"]).upper():
        tnum_keys = [
            "XY_XL",
            "XY_XH",
            "XY_YL",
            "XY_YH",
            "XY_Waf",
            "XY_Lot0",
            "XY_Lot1",
            "XY_Lot2",
            "XY_Lot3",
            "XY_Lot4",
            "XY_Lot5",
            "XY_Lot6",
        ]
        with open("src/jupiter/personalization.json", "r") as file:
            data = json.load(file)
        product_data = data.get(parameter["PRODUCT"], {})
        for key in tnum_keys:
            test_numbers.append(product_data.get(key, {}))

    if len(test_numbers) == 0:
        print(f"No tests found for composite: {composite}")
        uty.write_log(f"No tests found for composite: {composite}", FILENAME)
        return
    test_numbers_str = ", ".join(map(str, test_numbers))
    uty.write_log(f"Converting tests by test list", FILENAME)
    csv_files = stdf2csv(stdf_folder, csv_folder, f"-l {test_numbers_str}")
    if len(csv_files) == 0:
        print(f"No Extaction good : {composite}")
        uty.write_log(f"No Extaction good : {composite}", FILENAME)
        return
    parameter["COM"] = composite
    parameter["TEST_NUM"] = test_numbers
    parameter["CSV"] = csv_file

    debug and print(parameter)
    exec(parameter)


def process_single_composite(
    parameter, tsr, composite, csv_file, stdf_folder, csv_folder
):
    """
    Process a single composite and execute the report generation.

    Args:
        parameter (dict): Parameters for processing.
        tsr (DataFrame): DataFrame containing test results.
        composite (str): Composite name to process.
        csv_file (str): CSV file name to process.
    """
    match_group = tsr["TEST_NAM"].str.extract(
        r"(.*_{0}_.*:.*|.*_{0}_..$|.*_{0}_.*_DELTA_.*)".format(composite)
    )
    tsr["match_group"] = match_group[0]

    test_numbers = tsr.loc[tsr["match_group"].notnull(), "TEST_NUM"].unique().tolist()

    if "EWS" not in str(parameter["FLOW"]).upper():
        tnum_keys = [
            "XY_XL",
            "XY_XH",
            "XY_YL",
            "XY_YH",
            "XY_Waf",
            "XY_Lot0",
            "XY_Lot1",
            "XY_Lot2",
            "XY_Lot3",
            "XY_Lot4",
            "XY_Lot5",
            "XY_Lot6",
        ]
        with open("src/jupiter/personalization.json", "r") as file:
            data = json.load(file)
        product_data = data.get(parameter["PRODUCT"], {})
        for key in tnum_keys:
            test_numbers.append(product_data.get(key, {}))

    if len(test_numbers) == 0:
        print(f"No tests found for composite: {composite}")
        uty.write_log(f"No tests found for composite: {composite}", FILENAME)
        return
    test_numbers_str = ", ".join(map(str, test_numbers))
    uty.write_log(f"Converting tests by test list", FILENAME)
    csv_files = stdf2csv(stdf_folder, csv_folder, f"-l {test_numbers_str}")
    if len(csv_files) == 0:
        print(f"No Extaction good : {composite}")
        uty.write_log(f"No Extaction good : {composite}", FILENAME)
        return
    parameter["COM"] = composite
    parameter["TEST_NUM"] = test_numbers
    parameter["CSV"] = csv_file

    debug and print(parameter)
    exec(parameter)


def write_config_file(parameter):
    """
    Write the configuration parameters to a JSON file.

    Args:
        parameter (dict): Parameters for processing.
    """
    cfgfile = f"./src/jupiter/cfg.json"
    try:
        # Convert any Series objects in the parameter dictionary to lists
        parameter = {
            k: v.tolist() if isinstance(v, pd.Series) else v
            for k, v in parameter.items()
        }

        with open(cfgfile, mode="wt", encoding="utf-8") as file:
            json.dump(parameter, file, indent=4)
    except Exception as e:
        print(f"Error writing the configuration file: {e}")


def convert_notebook_to_html(parameter):
    """
    Convert the Jupyter notebook to HTML format.

    Args:
        parameter (dict): Parameters for processing.
    """
    uty.write_log("Start Jupyter conversion", FILENAME)
    timestartsub = datetime.datetime.now()
    if "EWS" in str(parameter["FLOW"]).upper():
        str_output = (
            parameter["TITLE"]
            + " "
            + parameter["FLOW"]
            + "_"
            + parameter["TYPE"].lower()
        )
    else:
        str_output = (
            parameter["TITLE"]
            + " "
            + parameter["FLOW"]
            + "_"
            + parameter["LOT"].split(" (")[1].replace("FT lot ", "_").replace(")", "")
            + "_"
            + parameter["TYPE"].lower()
        )
    if parameter["LOT"] != "-":
        dir_output = os.path.abspath(
            os.path.join(
                "\\\\gpm-pe-data.gnb.st.com\\ENGI_MCD_STDF",
                parameter["CODE"],
                parameter["FLOW"],
                f"{parameter['LOT'].split(' (')[0]}",
                f"{parameter['LOT'].split(' (')[0]}_{str(parameter['WAFER']).rjust(2, '0')}",
                parameter["TYPE"].upper(),
                "Report",
                parameter["TYPE"].upper(),
            )
        )
    else:
        dir_output = os.path.abspath(
            os.path.join(
                "\\\\gpm-pe-data.gnb.st.com\\ENGI_MCD_STDF",
                parameter["PRODUCT"],
                parameter["FLOW"],
            )
        )
    if not os.path.exists(dir_output):
        os.makedirs(dir_output)

    cmd = f'"C:\\Program Files\\Python\\python.exe" "C:\\Program Files\\Python\\Scripts\\jupyter-nbconvert.exe" ./src/jupiter/{str(parameter["TYPE"]).upper()}.ipynb --execute --no-input --to html --output "{dir_output}/{str_output}" '
    if (
        subprocess.call(
            args=cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
        )
        == 0
    ):
        pass
    else:
        print(f"ERROR: execution failed {cmd}")

    uty.write_log("DONE Jupyter conversion", FILENAME)

    return timestartsub, dir_output, str_output


def rework_report(parameter, dir_output, str_output):
    """
    Substitute HTML title with TITLE name and add CSS for better report aspect.

    Args:
        parameter (dict): Parameters for processing.
    """
    report_path = os.path.abspath(f"{dir_output}/{str_output}.html")

    title = parameter["TITLE"]
    new_str = (
        "<title>"
        + title
        + "</title>"
        + '<link rel="icon" href="https://www.st.com/etc/clientlibs/st-site/media/app/images/favicon.ico">'
        + '<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>'
    )

    try:
        # Utilizza PowerShell per sostituire la riga 6 del file HTML
        ps_command = f"""
        $filePath = "{report_path}"
        $newContent = "{new_str.replace('"', '`"')}"
        $lines = Get-Content $filePath
        $lines[5] = $newContent
        $lines | Set-Content $filePath
        """
        subprocess.run(
            ["powershell", "-Command", ps_command], check=True, text=True, shell=True
        )

        import webbrowser

        webbrowser.open(f"file://{report_path}")
    except Exception as e:
        uty.write_log(f"ERROR: rework_report {e}", FILENAME)
        print(f"ERROR: rework_report {e}")


def pre_exec(parameter):
    """
    Pre-execution function to handle STDF to CSV conversion and composite processing.

    Args:
        parameter (dict): Parameters for processing.
    """
    list_csv_files = []
    csv_folder = os.path.abspath("src/csv")
    print("|--> TITLE:", parameter["TITLE"])
    clearTmpSTDF()

    if parameter["WAFER"] == "all":
        process_all_wafers(parameter, csv_folder)
    elif "," in parameter["WAFER"]:
        process_multi_wafers(parameter, csv_folder)
    elif parameter["WAFER"] == "-" and str(parameter["TYPE"]).upper() == "CONDITION":
        stdf_path = parameter["FILE"].get("-").get("path")
        process_condition(parameter, parameter["COM"], stdf_path)
    else:
        process_single_wafer(parameter, csv_folder)

    uty.write_log("STDF2CSV DONE", FILENAME)


def exec(parameter):
    """
    Execute the report generation steps.

    Args:
        parameter (dict): Parameters for processing.
    """
    try:
        if (
            str(parameter["COM"].upper()) == "YIELD"
            or str(parameter["TYPE"]).upper() == "CONDITION"
        ):
            pass
        else:
            parameter = rework_stdf(parameter)
        write_config_file(parameter)
        timestartsub, dir_output, str_output = convert_notebook_to_html(parameter)
        post_exec(parameter, timestartsub, dir_output, str_output)
    except Exception as e:
        print(f"ERROR execution: {e}")


def post_exec(parameter, timestartsub, dir_output, str_output):
    """
    Post-execution function to handle final steps.

    Args:
        parameter (dict): Parameters for processing.
    """
    uty.write_log("postexec START", FILENAME)
    # rework_report(parameter, dir_output, str_output)
    clearTmpSTDF()
    uty.write_log("postexec DONE", FILENAME)
    timeendsub = datetime.datetime.now()
    timeexecsub = timeendsub - timestartsub
    print("Conversion time:", timeexecsub, "\n")


def generate(data):
    """Genrate forn HTML GUI"""
    timestart = datetime.datetime.now()
    author_info = data["authorInfo"]

    parameters = pd.DataFrame(
        [
            {
                **{k.upper(): v for k, v in entry.items()},
                **{k.upper(): v for k, v in author_info.items()},
            }
            for entry in data["data"]
            if entry["Run"] == "1"
        ]
    )
    parameters.index += 1
    print(parameters.to_string())
    print("\n")
    os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
    for _, parameter in parameters.iterrows():
        uty.write_log(f"START {parameter['TITLE']}", FILENAME)
        pre_exec(parameter)
        uty.write_log("DONE", FILENAME)
    timeend = datetime.datetime.now()
    timeexec = timeend - timestart
    uty.write_log("     ...     ", FILENAME)
    print("|--> Total execution time:", timeexec)


def main():
    """
    Main function to execute the report generation process.
    """
    global debug
    debug = False

    guihtml()

    # timestart = datetime.datetime.now()
    # parameters = read_parameters("workload.csv")
    # print(parameters)
    # os.environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
    # for _, parameter in parameters.iterrows():
    #     uty.write_log("START")
    #     pre_exec(parameter)
    # timeend = datetime.datetime.now()
    # timeexec = timeend - timestart
    # print("|--> Total execution time:", timeexec)


if __name__ == "__main__":
    print("\n\n--- REPORT GENERATOR ---")
    main()
    print("|-->END\n")
