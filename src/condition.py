
import os
import json
import fileinput
import subprocess
import pandas as pd

from bs4 import BeautifulSoup
from io import StringIO

file_path = '.\\STDF\\anaflow_VAL_ST44EZ_T2KF1_0007.html'

with open(file_path, 'r', encoding='utf-8') as file:
    soup = BeautifulSoup(file.read(), 'html.parser')

title = soup.find('h1').get_text().split(" ")[-1]
df = pd.read_html(StringIO(str(soup.find('table'))))[0]

df = df.dropna(how='all')
df[['Tag', 'SB', 'HB', 'Byp']] = df[['Tag', 'SB', 'HB', 'Byp']].fillna(0).astype(int)

df = df[df['Tag'] == 1]
df = df[df['Byp'] == 0]
df['Testsuite'] = df['Testsuite'].str.upper()
df['HB Name'] = df['HB Name'].str.replace('_', '')
df = df[~df['Testsuite'].str.contains('TTIME')]

df['Testsuite'] = df.apply(lambda row: row['Testsuite'].replace(row['Comp'].upper(), '').split('__')[0], axis=1)
df = df.drop(columns=['Ext', 'Byp', 'Tag'])
df.reset_index(drop=True, inplace=True)

parameter = {
        "TITLE": "MBIST",
        "COM": "mbist",
        "FLOW": "EWS1",
        "TYPE": "STD",
        "PRODUCT": "Mosquito512K",
        "CODE": "44E",
        "LOT": "P6AX86",
        "WAFER": "1",
        "AUTHOR": "Matteo Terranova",
        "MAIL": "matteo.terranova@st.com",
        "GROUP": "MDRF - EP - GPAM",
        "Cut": "2.1",
        "SITE": "Catania",
        "REVISION": "0.1",
        "stdf": "example.com",
        "RUN": "1",
        "TEST_NUM": ["80003000", "80004000"],
        "CSV": "r44exxxz_q443616_04_st44ez-t2kf1_e_ews1_tat2k06_20250301214005.std",
    }

for comp_value in df['Comp'].unique():
    df_comp = df[df['Comp'] == comp_value]
    filename = f"./src/tmp/condition.csv"
    df_comp.to_csv(filename, index=False)
    parameter["TITLE"] = comp_value
    parameter["COM"] = comp_value
    parameter["TYPE"] = 'CONDITION'
    parameter["FLOW"] = 'EWS1'
    print(comp_value)
    cfgfile = f"./src/jupiter/cfg.json"
    try:
        # Convert any Series objects in the parameter dictionary to lists
        parameter = {k: v.tolist() if isinstance(v, pd.Series) else v for k, v in parameter.items()}
        
        with open(cfgfile, mode="wt", encoding="utf-8") as file:
            json.dump(parameter, file, indent=4)
    except Exception as e:
        print(f"Error writing the configuration file: {e}")

    str_output = (
        parameter["TITLE"] + " " + parameter["FLOW"] + "_" + parameter["TYPE"].lower()
    )
    dir_output = os.path.abspath(
        os.path.join(
            "Report",
            f"{parameter['PRODUCT']}",
            parameter["FLOW"],
            parameter["TYPE"].upper(),
        )
    )
    if not os.path.exists(dir_output):
        os.makedirs(dir_output)

    cmd = f'jupyter nbconvert --execute --no-input --to html --output "{dir_output}/{str_output}" ./src/jupiter/{str(parameter["TYPE"]).upper()}.ipynb'
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
