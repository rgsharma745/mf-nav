import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests

URL_FORMAT = 'https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt={date}'
EXPECTED_RESPONSE_START = "Scheme Code;Scheme Name;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Net Asset Value;Repurchase Price;Sale Price;Date"

scheme_to_filter = {122639, 119598, 119544, 119065, 120468, 119598, 119212, 120465, 105989, 120684, 118473, 120828,
                    118950, 120833, 152712, 149219, 120847, 151130, 151750, 118473, 145552, 148662, 152156, 152843,
                    120620, 127042}


def fetch_nav_from_amfi(date):
    date_str = validate_and_format_date(date)
    if not date_str:
        print("Date is not valid")
        return None

    nav_data = fetch_nav_data(date_str)
    if not nav_data:
        print('Error fetching NAV data')
        return None

    for line in nav_data:
        process_line(line, date)


def validate_and_format_date(date):
    try:
        return datetime.strptime(date, "%d-%m-%Y").strftime("%d-%b-%Y")
    except ValueError:
        print(f'Invalid Date : {date}')
        return None


def fetch_nav_data(date_str):
    print(URL_FORMAT.format(date=date_str))
    response = requests.get(URL_FORMAT.format(date=date_str))
    if response.status_code != 200:
        print('Error calling AMFI Request')
        return None

    response_text = response.text
    if not response_text.startswith(EXPECTED_RESPONSE_START):
        print('Data Not Available')
        return None

    return response_text.split('\n')


def process_line(line, date):
    if len(re.findall(";", line)) == 7:
        result = line.split(";")
        if result[0] != 'Scheme Code' and int(result[0]) in scheme_to_filter:
            #print(line)
            scheme_code = result[0]
            nav = result[4]
            write_data_files(scheme_code, nav, date)


def write_data_files(scheme_code, nav, date):
    parent_dir = f'./data/{scheme_code}'
    Path(parent_dir).mkdir(parents=True, exist_ok=True)
    write_file( scheme_code, nav)


def is_today_date(date):
    return datetime.strptime(date, "%d-%m-%Y").strftime("%d-%m-%Y") == datetime.today().strftime("%d-%m-%Y")


def write_file( scheme_code, nav):
    file_name_latest = f'./data/{scheme_code}/latest'
    file_name_prev = f'./data/{scheme_code}/previous'
    if os.path.exists(file_name_latest):
        if os.path.exists(file_name_prev):
            os.remove(file_name_prev)
        os.rename(file_name_latest, file_name_prev)
    with open(file_name_latest, 'w') as file:
        file.write(nav)



def last_working_day(days_to_minus):
    today = datetime.today()
    day_of_week = today.weekday()
    if day_of_week == 6:
        last_working_date = today - timedelta(days=2 + days_to_minus)
    elif day_of_week == 5:
        last_working_date = today - timedelta(days=1 + days_to_minus)
    else:
        last_working_date = today -  timedelta(days=1 + days_to_minus)
    return last_working_date.strftime("%d-%m-%Y")

if __name__ == '__main__':
    fetch_nav_from_amfi(last_working_day(1))
    fetch_nav_from_amfi(last_working_day(0))
    fetch_nav_from_amfi(datetime.today().strftime("%d-%m-%Y"))
