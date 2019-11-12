import urllib.request
import pandas as pd
from bs4 import BeautifulSoup
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

    # going through all the columns and specifying data types
    df["Laps"] = pd.to_numeric(df["Laps"], errors='coerce').astype('Int64')
    df["Grand Prix"] = df["Grand Prix"].astype(str)
    df["Winner"] = df["Winner"].astype(str).apply(lambda x: x.replace(" ", ""))
    df["Car"] = df["Car"].astype(str)
    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S.%f").dt.time
    return df


def create_race_dataframe(table):
    """
    Create race dataframe from results table
    :param table: results table from create_results_table() func
        Actually a list of lists!
    :return: race dataframe
    """
    df = pd.DataFrame(table[1:], columns=table[0])  # creating dataframe

    # going through all the columns and specifying data types
    df["Pos"] = pd.to_numeric(df["Pos"], errors='coerce').astype('Int64')
    df["No"] = df["No"].astype(int)
    df["Laps"] = pd.to_numeric(df["Laps"], errors='coerce').astype('Int64')
    df["Car"] = df["Car"].astype(str)
    df["Driver"] = df["Driver"].astype(str).apply(lambda x: x.replace(" ", ""))
    df["PTS"] = pd.to_numeric(df["PTS"], errors='coerce').astype('Int64')
    return df


def load_data_to_database(dataframe, table_name: str, engine):
    """
    Creates a table from provided dataframe in specified database with specified name
    Overwrites existing table!
    :param dataframe: dataframe to create table from
    :param table_name: name of the table
    :param engine: where to create table
    """
    sql_options = dict(if_exists='replace', index=False, method='multi')
    dataframe.to_sql(table_name, engine, **sql_options)  # truncates the table


db_engine, sql_session, sql_base = create_database()

race_number = 94  # arbitrary number from which FIA starts their race count
for season_year in range(1950, 1951):
    soup = BeautifulSoup(urllib.request.urlopen(create_year_url(season_year)), features="lxml")
    season_table = create_results_table(soup)
    season_df = create_season_dataframe(season_table)

    print(season_df)

    season_name = "{}_season".format(season_year)
    load_data_to_database(season_df, season_name, db_engine)

    grand_prixes = [gp.replace(' ', '-') for gp in season_df["Grand Prix"]]

    for gp in grand_prixes:
        soup = BeautifulSoup(urllib.request.urlopen(create_race_result_url(season_year, race_number, gp)),
                             features="lxml")
        gp_table = create_results_table(soup)
        gp_df = create_race_dataframe(gp_table)
        print(gp_df)
        print(gp_df.dtypes)

        gp_name = "{}_{}".format(season_year, gp)
        load_data_to_database(gp_df, gp_name, db_engine)

        race_number += 1

