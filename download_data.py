import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
from sql_handle import create_database


def create_year_url(year: int):
    """
    Create url for each season
    :param year: season year
    :return: full url
    """
    url = "https://www.formula1.com/en/results.html/{}/races.html".format(year)
    return url


def create_race_result_url(year: int, number: int, race: str):
    """
    Create url for each race
    :param year: season year
    :param number: race number
    :param race: race name
    :return: full url
    """
    url = "https://www.formula1.com/en/results.html/{}/races/{}/{}/race-result.html".format(year, number, race.lower())
    return url


def strip_row(raw_row):
    """
    Clean up the row from pure html table
    """
    return [cell.get_text(strip=True) for cell in raw_row if cell.get_text(strip=True) != '']


def create_results_table(html_soup):
    """
    Creating results table from html page
    Works for both seasons and races
    :param html_soup: html page
    :return: list of row lists
    """
    table = html_soup.find("table", {'class': 'resultsarchive-table'})  # finding the results table
    rows = table.find_all("tr")  # find all rows
    head_row = strip_row(table.find_all("th"))  # find header row
    results_table = []
    
    if head_row:
        results_table.append(head_row)
        rows = rows[1:]

    for row in rows:
        results_table.append(strip_row(row.find_all("td")))

    return results_table


def create_season_dataframe(table):
    """
    Create season dataframe from results table
    :param table: results table from create_results_table() func
        Actually a list of lists!
    :return: season dataframe
    """
    df = pd.DataFrame(table[1:], columns=table[0])  # creating dataframe

    # going through all the columns and specifying data types because pandas cannot do it more beautifully
    df["Laps"] = df["Laps"].astype(int)
    df["Grand Prix"] = df["Grand Prix"].astype(str)
    df["Winner"] = df["Winner"].astype(str)
    df["Car"] = df["Car"].astype(str)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S.%f").dt.time
    return df
    

sql_engine, sql_session, sql_base = create_database()
sql_options = dict(if_exists='replace', index=False, method='multi')
race_number = 94  # arbitrary number from which FIA starts their race count
for season_year in range(1950, 1951):
    soup = BeautifulSoup(urllib.request.urlopen(create_year_url(season_year)), features="lxml")
    season_table = create_results_table(soup)
    season_df = create_season_dataframe(season_table)

    print(season_df)
    print(season_df.dtypes)

    season_df.to_sql(str(season_year) + "_season", sql_engine, **sql_options)  # truncates the table

    grand_prixes = [gp.replace(' ', '-') for gp in season_df["Grand Prix"]]

    for gp in grand_prixes:
        soup = BeautifulSoup(urllib.request.urlopen(create_race_result_url(season_year, race_number, gp)),
                             features="lxml")

        gp_table = create_results_table(soup)
        gp_df = pd.DataFrame(gp_table[1:], columns=gp_table[0])
        print(gp_df)

        gp_df.to_sql(str(season_year) + '_' + gp, sql_engine, **sql_options)

        race_number += 1

