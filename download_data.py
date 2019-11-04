import urllib.request
from bs4 import BeautifulSoup
import pandas as pd


def create_year_url(year: int):
    url = "https://www.formula1.com/en/results.html/{}/races.html".format(year)
    return url


def create_race_result_url(year, number, race):
    url = "https://www.formula1.com/en/results.html/{}/races/{}/{}/race-result.html".format(year, number, race.lower())
    return url


def strip_row(raw_row):
    return [cell.get_text(strip=True) for cell in raw_row if cell.get_text(strip=True) != '']


def get_results_table(url_soup):
    table = url_soup.find("table", {'class': 'resultsarchive-table'})
    rows = table.find_all("tr")
    head_row = strip_row(table.find_all("th"))

    res_table = []
    if head_row:
        res_table.append(head_row)
        rows = rows[1:]

    for row in rows:
        res_table.append(strip_row(row.find_all("td")))

    return res_table


race_number = 94  # arbitrary number from which FIA starts their race count
for championship_year in range(1950, 1960):
    soup = BeautifulSoup(urllib.request.urlopen(create_year_url(championship_year)), features="lxml")

    year_table = get_results_table(soup)
    year_df = pd.DataFrame(year_table[1:], columns=year_table[0])
    print(year_df)

    grand_prixes = [gp.replace(' ', '-') for gp in year_df["Grand Prix"]]
    print(grand_prixes)

    for gp in grand_prixes:
        soup = BeautifulSoup(urllib.request.urlopen(create_race_result_url(championship_year, race_number, gp)),
                             features="lxml")

        gp_table = get_results_table(soup)
        gp_df = pd.DataFrame(gp_table[1:], columns=gp_table[0])
        print(gp_df)

        race_number += 1

