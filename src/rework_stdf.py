import os
import sys
import datetime
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "jupiter"))
import utility as uty

sys.path.pop()

debug = False

FILENAME = os.path.abspath("src/run.log")

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


def rework_stdf(parameter):
    # print(parameter)
    composite = parameter["COM"]
    flwtp = parameter["TYPE"]
    groosgood30 = 0
    p = os.listdir()
    ptr = pd.DataFrame()
    ftr = pd.DataFrame()
    population = pd.DataFrame()
    ptr_dict = {}
    ftr_dict = {}
    ptrtname = []
    ftrtname = []
    uty.write_log("Rework STDF START", FILENAME)
    pd.set_option("display.width", None)

    # ----------==================================================---------- #
    # Read extracted file
    # ----------==================================================---------- #

    test_nums = parameter["TEST_NUM"] if isinstance(parameter["TEST_NUM"], list) else [parameter["TEST_NUM"]]
    
    # PTR Parametric Test Record
    tmpptr = pd.read_csv(
        os.path.abspath(f"./src/csv/{parameter['CSV']}.ptr.csv"),
        usecols=[0, 1, 3, 6, 7, 10, 13, 14, 15],
    )
    tmpptr = tmpptr[tmpptr["TEST_NUM"].isin(test_nums)]
    uty.write_log("    READ PTR", FILENAME)

    # FTR Functional Test Record
    tmpftr = pd.read_csv(f"./src/csv/{parameter['CSV']}.ftr.csv", usecols=[0, 1, 4, 23])
    tmpftr = tmpftr[tmpftr["TEST_NUM"].isin(test_nums)]
    uty.write_log("    READ FTR", FILENAME)

    # MIR Master Information Record
    mir = pd.read_csv(f"./src/csv/{parameter['CSV']}.mir.csv")
    # PRR Part Results Record
    prr = pd.read_csv(f"./src/csv/{parameter['CSV']}.prr.csv")
    # PCR Part Count Record
    pcr = pd.read_csv(f"./src/csv/{parameter['CSV']}.pcr.csv")
    # HBR Hardware Bin Record
    hbr = pd.read_csv(f"./src/csv/{parameter['CSV']}.hbr.csv")
    # SBR Software Bin Record
    sbr = pd.read_csv(f"./src/csv/{parameter['CSV']}.sbr.csv")

    # ----------==================================================---------- #
    uty.write_log("   Read STDF", FILENAME)
    # ----------==================================================---------- #
    # round to nearest 5 temperature
    # ----------==================================================---------- #

    if str(mir["TST_TEMP"].iloc[0]) == "nan":
        mir["TST_TEMP"] = "30"

    temperature = int(round(float(mir["TST_TEMP"].iloc[0]) / 5.0) * 5.0)
    tmpptr["TEMPERATURE"] = temperature
    tmpftr["TEMPERATURE"] = temperature

    # ----------==================================================---------- #
    tmpptr["WAFER"] = mir.SBLOT_ID[0]
    tmpftr["WAFER"] = mir.SBLOT_ID[0]
    tmpptr["LOT_ID"] = mir.LOT_ID[0]
    tmpftr["LOT_ID"] = mir.LOT_ID[0]
    # ----------==================================================---------- #

    # ----------==================================================---------- #
    gross = pcr[pcr["HEAD_NUM"] == 255]["PART_CNT"].values[0]
    goodPart = pcr[pcr["HEAD_NUM"] == 255]["GOOD_CNT"].values[0]
    ye = str(round(((goodPart * 100) / gross), 2)) + " %"
    population[temperature] = [goodPart, gross, ye]
    # print(ptr)

    # ----------==================================================---------- #
    # Remove retest
    # ----------==================================================---------- #
    if str(parameter["TYPE"]).upper() != "X30":
        prr = prr.drop_duplicates(subset=["X_COORD", "Y_COORD"], keep="last")
        # ----------==================================================---------- #

        tmpptr = tmpptr.merge(
            prr[["PartID", "X_COORD", "Y_COORD", "SOFT_BIN", "HARD_BIN"]],
            how="inner",
            on="PartID",
        )
        tmpftr = tmpftr.merge(
            prr[["PartID", "X_COORD", "Y_COORD"]],
            how="inner",
            on="PartID",
        )
        # ----------==================================================---------- #
        # Print retest
        # print(corner,str(mir.SBLOT_ID[0]),str(int(
        #     round(float(mir["TST_TEMP"].iloc[0]) / 5.0) * 5.0
        # )), tmpptr['PartID'].max()-prr.shape[0])

    # ----------==================================================---------- #
    # Remove ususefull Test
    # ----------==================================================---------- #
    tmpptr = tmpptr[~tmpptr["TEST_TXT"].str.startswith(("R_", "log"))]
    tmpptr = tmpptr[
        ~tmpptr["TEST_TXT"].str.contains("OTPWord|TestTime|XId|YId|WaferId")
    ]
    tmpftr = tmpftr[~tmpftr["TEST_TXT"].str.startswith(("R_", "log"))]
    tmpftr = tmpftr[
        ~tmpftr["TEST_TXT"].str.contains("OTPWord|TestTime|XId|YId|WaferId")
    ]

    # ----------==================================================---------- #
    # FIX ERROR
    # ----------==================================================---------- #
    if composite == "scan":
        tmpptr = tmpptr[~tmpptr["TEST_TXT"].str.contains("Stress")]
    if composite == "RB":
        tmpptr = tmpptr[~tmpptr["TEST_TXT"].str.contains("diff", case=False)]
    if composite == "RNG":
        tmpptr = tmpptr[~tmpptr["TEST_TXT"].str.contains("div", case=False)]
    if composite == "Register_Test":
        tmpptr.loc[tmpptr["TEST_NUM"] == 90020000, "HI_LIMIT"] = 1.5
        tmpptr.loc[tmpptr["TEST_NUM"] == 90020000, "LO_LIMIT"] = 0.5

    # ----------==================================================---------- #
    uty.write_log("   Cleaning", FILENAME)
    # ----------==================================================---------- #
    # Data Paipeline cleaning
    # ----------==================================================---------- #

    # ----------==================================================---------- #
    # Inizialize variable
    # testv33 = pd.DataFrame()
    testvdd = pd.DataFrame()
    testv11 = pd.DataFrame()
    test = pd.DataFrame()
    # ----------==================================================---------- #

    # ----------==================================================---------- #
    # START CLEANING PARAMETRIC TEST RECORD
    if not tmpptr.empty:

        # ----------==================================================---------- #
        # Rework RESULT SCALE
        if not tmpptr.empty:

            debug and uty.write_log("      A", FILENAME)

            tmpptr["RES_SCAL"] = tmpptr.groupby("TEST_TXT")["RES_SCAL"].transform("max")
    
            # Cast to string before concatenation
            tmpptr["UNITS"] = tmpptr["UNITS"].astype(str)
            tmpptr.loc[tmpptr["RES_SCAL"] == 3, "UNITS"] = "m" + tmpptr.loc[tmpptr["RES_SCAL"] == 3, "UNITS"]
            tmpptr.loc[tmpptr["RES_SCAL"] == 6, "UNITS"] = "u" + tmpptr.loc[tmpptr["RES_SCAL"] == 6, "UNITS"]
            tmpptr.loc[tmpptr["RES_SCAL"] == 9, "UNITS"] = "n" + tmpptr.loc[tmpptr["RES_SCAL"] == 9, "UNITS"]
            tmpptr.loc[tmpptr["RES_SCAL"] == 12, "UNITS"] = "p" + tmpptr.loc[tmpptr["RES_SCAL"] == 12, "UNITS"]
            tmpptr.loc[tmpptr["RES_SCAL"] == 15, "UNITS"] = "f" + tmpptr.loc[tmpptr["RES_SCAL"] == 15, "UNITS"]
            tmpptr.loc[tmpptr["RES_SCAL"] == 18, "UNITS"] = "a" + tmpptr.loc[tmpptr["RES_SCAL"] == 18, "UNITS"]
            tmpptr.loc[tmpptr["RES_SCAL"] == -3, "UNITS"] = "K" + tmpptr.loc[tmpptr["RES_SCAL"] == -3, "UNITS"]
            tmpptr.loc[tmpptr["RES_SCAL"] == -6, "UNITS"] = "M" + tmpptr.loc[tmpptr["RES_SCAL"] == -6, "UNITS"]
            tmpptr.loc[tmpptr["RES_SCAL"] == -9, "UNITS"] = "G" + tmpptr.loc[tmpptr["RES_SCAL"] == -9, "UNITS"]

            debug and uty.write_log("      B", FILENAME)

            tmpptr["RESULT"] = tmpptr["RESULT"].astype(float)
            tmpptr["HI_LIMIT"] = tmpptr["HI_LIMIT"].astype(float)
            tmpptr["LO_LIMIT"] = tmpptr["LO_LIMIT"].astype(float)
            
            # Ensure the results are cast to float
            tmpptr.loc[:, "RESULT"] = round(
                tmpptr["RESULT"] * tmpptr["RES_SCAL"].apply(power_of_10), 3
            ).astype(float)
            tmpptr.loc[:, "HI_LIMIT"] = round(
                tmpptr["HI_LIMIT"] * tmpptr["RES_SCAL"].apply(power_of_10),
                3,
            ).astype(float)
            tmpptr.loc[:, "LO_LIMIT"] = round(
                tmpptr["LO_LIMIT"] * tmpptr["RES_SCAL"].apply(power_of_10),
                3,
            ).astype(float)

        # ----------==================================================---------- #

        uty.write_log("Result Scale done", FILENAME)

        # ----------==================================================---------- #
        # SPLIT VDD TESTS
        regex = f"(?P<TestName>.*)(_vio_|_vbt_|_v11_)(?P<VDD>[^_]+)_(?P<COM>{composite})_(?P<TARGET>.*)"
        # work in a copy dataframe
        testvdd = tmpptr.loc[tmpptr["TEST_TXT"].str.match(regex)].copy()
        # execute split test name
        testvdd[["TestName", "tmpvdd", "Volt", "COM", "TARGET"]] = testvdd[
            "TEST_TXT"
        ].str.extract(regex, expand=True)
        # remove all unusefull test
        testvdd = testvdd.dropna(subset=["TestName"])
        testvdd["pltype"] = "BPLVDD"
        # remove in test all
        if not testvdd.empty:
            tmpptr = tmpptr.loc[~tmpptr["TEST_TXT"].str.match(regex)]
        # print(testvdd)
        # ----------==================================================---------- #

        # ----------==================================================---------- #
        # SPLIT STANDARD TEST
        regex = f"(?P<TestName>.*)_(?P<COM>{composite})_(?P<TARGET>.*)"
        test = tmpptr.copy()
        test[["TestName", "COM", "TARGET"]] = test["TEST_TXT"].str.extract(
            regex, expand=True
        )
        test["pltype"] = "BPLTEMP"
        test = test[test["COM"].notna()]
        # uty.write_log("Rework FTR all test done", FILENAME)
        # ----------==================================================---------- #

        uty.write_log("PTR Split VDD done", FILENAME)

        # ----------==================================================---------- #
        # Choosing the Chart Type
        clearptr = pd.concat([test, testvdd])

        regex = "(.*(:.*))|(.*)"
        if not clearptr.empty:
            clearptr[["tmp", "TARGET", "FTYPE"]] = clearptr["TARGET"].str.extract(
                regex, expand=True
            )
            clearptr.pop("tmp")
            clearptr.fillna({"TARGET": ""}, inplace=True)
            clearptr["TEST_TXT"] = (
                clearptr.pop("TestName").str.upper() + clearptr["TARGET"]
            )
            clearptr.loc[
                clearptr["TARGET"].str.contains("Trim", case=False),
                "pltype",
            ] = "TRIM"
            clearptr = clearptr.drop(
                clearptr[clearptr["TARGET"].str.contains("TestTime")].index
            )

            clearptr.rename(
                columns={
                    "RESULT": "Value",
                    "LO_LIMIT": "Low Limit",
                    "HI_LIMIT": "High Limit",
                    "UNITS": "Unit",
                    "TEMPERATURE": "°C",
                    "TEST_NUM": "TestNumber",
                    "CORNER": "Corner",
                    "TEST_TXT": "TestName",
                },
                inplace=True,
            )
            clearptr = clearptr.drop(["LOT_ID", "TARGET"], axis=1)
            clearptr.fillna({"Volt": "Standard"}, inplace=True)
            ptr_dict[parameter["CSV"]] = clearptr
            # ptrtname = clearptr["TestName"].unique()
            # uty.write_log("PTR all done", FILENAME)
        # ----------==================================================---------- #

        # ----------==================================================---------- #
        # CLEANING SHEREDE VAR
        testvdd = pd.DataFrame()
        test = pd.DataFrame()
        # ----------==================================================---------- #

    uty.write_log("END PTR", FILENAME)

    # ----------==================================================---------- #
    if not tmpftr.empty:
        # ----------==================================================---------- #
        # SPLIT VDD TESTS
        regex = f"(?P<TestName>.*)(_vio_|_vbt_|_v11_)(?P<VDD>[^_]+)_(?P<COM>{composite})_(?P<TARGET>.*)"
        testvdd = tmpftr.loc[tmpftr["TEST_TXT"].str.match(regex)].copy()
        testvdd[["TestName", "tmpvdd", "Volt", "COM", "TARGET"]] = testvdd[
            "TEST_TXT"
        ].str.extract(regex, expand=True)
        testvdd["pltype"] = "BPLVDD"
        if not testvdd.empty:
            tmpftr = tmpftr.loc[~tmpftr["TEST_TXT"].str.match(regex)]
        # uty.write_log("Rework ftr Vdd done", FILENAME)
        # ----------==================================================---------- #

        # ----------==================================================---------- #
        # SPLIT STANDARD TEST
        regex = f"(?P<TestName>.*)_(?P<COM>{composite})_(?P<TARGET>.*)"
        test = tmpftr.copy()
        test[["TestName", "COM", "TARGET"]] = test["TEST_TXT"].str.extract(
            regex, expand=True
        )
        test["pltype"] = "BPLTEMP"
        test = test[test["COM"].notna()]
        # uty.write_log("Rework FTR all test done", FILENAME)
        # ----------==================================================---------- #

        # ----------==================================================---------- #

        # clearftr = pd.concat(
        #     [testvdd]  # ONLY SPECIAL VDD ARE COMPUTED, STD TEST ARE IGNORED
        # )
        clearftr = pd.concat([test, testvdd])

        if not clearftr.empty:
            clearftr["TEST_TXT"] = (
                clearftr.pop("TestName").str.upper()
            )
            clearftr.rename(
                columns={
                    "TEMPERATURE": "°C",
                    "TEST_NUM": "TestNumber",
                    "CORNER": "Corner",
                    "TEST_TXT": "TestName",
                },
                inplace=True,
            )
            clearftr = clearftr.drop(["LOT_ID", "TARGET", "tmpvdd"], axis=1)
            clearftr.fillna({"Volt": "Standard"}, inplace=True)
            # Create Result (1 = test PASS) (0 = test FAIL)
            # That's because we print the passes, so we just have to count
            clearftr["RESULT"] = (
                clearftr["TEST_FLG"]
                .apply(lambda x: int(str(x)[-8]) if len(str(x)) >= 8 else 0)
                .apply(lambda x: 1 if x == 0 else 0 if x == 1 else "N/A")
            )
            ftr_dict[parameter["CSV"]] = clearftr
            # ftrtname = clearftr["TestName"].unique()
            # uty.write_log("FTR all done", FILENAME)
        # ----------==================================================---------- #

    uty.write_log("END FTR", FILENAME)

    if len(ptr_dict) != 0:
        ptr = pd.concat(ptr_dict.values(), ignore_index=True)
    if len(ftr_dict) != 0:
        ftr = pd.concat(ftr_dict.values(), ignore_index=True)

    if os.path.exists(f"./src/tmp"):
        pass
    else:
        os.makedirs("./src/tmp", exist_ok=True)

    ptr.to_csv(os.path.abspath("./src/tmp/ptr.csv"), index=False)
    ftr.to_csv(os.path.abspath("./src/tmp/ftr.csv"), index=False)

    uty.write_log("Rework STDF DONE", FILENAME)

def main():

    with open("src/jupiter/cfg.txt", "r") as file:
        content = file.read()
        lines = content.split("\n")
        parameter = {
            "TITLE": "MBIST",
            "COM": "mbist",
            "FLOW": "EWS",
            "TYPE": "STD",
            "PRODUCT": "Mosquito",
            "CODE": "44E",
            "LOT": "P6AX86",
            "WAFER": "1",
            "Author": "Matteo Terranova",
            "Mail": "matteo.terranova@st.com",
            "Cut": "2.1",
            "Site": "Catania",
            "stdf": "example.com",
            "RUN": "1",
            "TEST_NUM": ["80003000", "80004000"],
            "CSV": "04_r498xxxz_p6ax86_01_st498z-t2kf1_e_ews1_tat2k11_20231222165236_030.std",
        }
        for line in lines:
            if len(line) > 1:
                key, value = line.split(":")
                parameter[key] = value

    rework_stdf(parameter)


if __name__ == "__main__":
    last_timestamp = datetime.datetime.now()
    main()
