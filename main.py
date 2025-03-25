import csv
import os
import re
from datetime import datetime, timedelta
from typing import IO

import requests

URL_FORMAT = 'https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt={date}'
EXPECTED_RESPONSE_START = "Scheme Code;Scheme Name;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Net Asset Value;Repurchase Price;Sale Price;Date"

scheme_to_filter = {122639, 119598, 119544, 119065, 120468, 119598, 119212, 120465, 105989, 120684, 118473, 120828,
                    118950, 120833, 152712, 149219, 120847, 151130, 151750, 118473, 145552, 148662, 152156, 152843,
                    120620, 127042, 148595, 152844}


def fetch_nav_from_amfi(date, data):
    date_str = validate_and_format_date(date)
    if not date_str:
        print("Date is not valid")
        return None

    nav_data = fetch_nav_data(date_str)
    if not nav_data:
        print('Error fetching NAV data')
        return None

    for line in nav_data:
        process_line(line, date, data)


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


def process_line(line, date, data):
    if len(re.findall(";", line)) == 7:
        result = line.split(";")
        if result[0] != 'Scheme Code' and int(result[0]) in scheme_to_filter:
            # print(line)
            scheme_code = result[0]
            scheme_name = result[1]
            nav = result[4]
            update_data(data, scheme_code, scheme_name, date, nav)


def load_data(filename):
    data = {}
    if os.path.exists(filename):
        with open(filename, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                scheme_code = row['SCHEME_CODE']
                data[scheme_code] = {
                    "SCHEME_NAME": row['SCHEME_NAME'],
                    "LATEST_DATE": row['LATEST_DATE'],
                    "LATEST_NAV": row['LATEST_NAV'],
                    "PREVIOUS_DATE": row['PREVIOUS_DATE'],
                    "PREVIOUS_NAV": row['PREVIOUS_NAV'],
                    "% CHANGE": row['% CHANGE'],
                }
    return data


def save_data(filename, data):
    with open(filename, mode='w', newline='') as file:
        fieldnames = ['SCHEME_CODE', 'SCHEME_NAME', 'LATEST_DATE', 'LATEST_NAV', 'PREVIOUS_DATE', 'PREVIOUS_NAV',
                      "% CHANGE"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for scheme_code in sorted(data.keys()):
            values = data[scheme_code]
            writer.writerow({
                'SCHEME_CODE': scheme_code,
                'SCHEME_NAME': values['SCHEME_NAME'],
                'LATEST_DATE': values['LATEST_DATE'],
                'LATEST_NAV': values['LATEST_NAV'],
                'PREVIOUS_DATE': values['PREVIOUS_DATE'],
                'PREVIOUS_NAV': values['PREVIOUS_NAV'],
                '% CHANGE': values['% CHANGE']
            })


# Function to update the data
def update_data(data, scheme_code, scheme_name, latest_date, latest_nav):
    if scheme_code not in data:
        data[scheme_code] = {
            "SCHEME_NAME": scheme_name,
            "LATEST_DATE": latest_date,
            "LATEST_NAV": latest_nav,
            "PREVIOUS_DATE": None,
            "PREVIOUS_NAV": None
        }
    elif data[scheme_code]["LATEST_DATE"] != latest_date:
        data[scheme_code]["SCHEME_NAME"] = scheme_name
        data[scheme_code]["PREVIOUS_DATE"] = data[scheme_code]["LATEST_DATE"]
        data[scheme_code]["PREVIOUS_NAV"] = data[scheme_code]["LATEST_NAV"]
        data[scheme_code]["LATEST_DATE"] = latest_date
        data[scheme_code]["LATEST_NAV"] = latest_nav
        data[scheme_code]["% CHANGE"] = round(((float(data[scheme_code]["LATEST_NAV"]) - float(
            data[scheme_code]["PREVIOUS_NAV"])) / float(data[scheme_code]["LATEST_NAV"])) * 100, 2)


def last_working_day(days_to_minus):
    today = datetime.today()
    day_of_week = today.weekday()
    if day_of_week == 6:
        last_working_date = today - timedelta(days=2 + days_to_minus)
    elif day_of_week == 5:
        last_working_date = today - timedelta(days=1 + days_to_minus)
    else:
        last_working_date = today - timedelta(days=1 + days_to_minus)
    return last_working_date.strftime("%d-%m-%Y")


if __name__ == '__main__':
    csv_data = load_data('./data/nav.csv')
    fetch_nav_from_amfi(last_working_day(1), csv_data)
    fetch_nav_from_amfi(last_working_day(0), csv_data)
    fetch_nav_from_amfi(datetime.today().strftime("%d-%m-%Y"), csv_data)
    save_data('./data/nav.csv', csv_data)
