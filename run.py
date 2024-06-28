"""
The main application file used to run the program.

Imports the necessary classes/functions from the following modules:
- gsheets.py
- scraper.py
"""

import pandas as pd
from scraper import Scraper, Crag
from gsheets import GoogleSheetsClient


def compile_data(crag: Crag):
    """
    Compile data from a Crag instance into pandas DataFrames for boulders,
    routes, and ascents.

    Args:
        crag (Crag): An instance of the Crag class containing the scraped data.

    Returns:
        Three pandas DataFrames:
            - boulder_data: DataFrame with boulder information.
            - route_data: DataFrame with route information.
            - ascent_data: DataFrame with ascent information.
    """

    # Create a DataFrame for boulders with their names, URLs,
    # and lists of associated routes
    boulder_data = pd.DataFrame([(b.name,
                                  b.url,
                                  [route.name for route in b.routes])
                                 for b in crag.boulders],
                                columns=["Boulder Name",
                                         "Boulder URL",
                                         "Route List"])

    # Initialize lists to hold route and ascent data
    route_data = []
    ascent_data = []

    # Iterate through each boulder in the crag
    for boulder in crag.boulders:
        # Iterate through each route in the current boulder
        for route in boulder.routes:
            # Append route information to route_data list
            route_data.append(
                (route.name,
                 boulder.name,
                 route.url,
                 route.grade,
                 route.ascents,
                 route.rating))
            # Iterate through each ascent log in the current route
            for ascent in route.ascent_log:
                # Append ascent information to ascent_data list
                ascent_data.append(
                    (route.name,
                     boulder.name,
                     ascent['climber_name'],
                     ascent['ascent_type'],
                     ascent['ascent_date'].strftime('%Y-%m-%d')))

    # Create DataFrame for route data
    route_data = pd.DataFrame(
        route_data,
        columns=["Route Name",
                 "Boulder Name",
                 "Route URL",
                 "Grade",
                 "Ascents",
                 "Rating"])

    # Create DataFrame for ascent data
    ascent_data = pd.DataFrame(
        ascent_data,
        columns=["Route Name",
                 "Boulder Name",
                 "Climber Name",
                 "Ascent Type",
                 "Ascent Date"])

    return boulder_data, route_data, ascent_data


def main():
    """
    The main application function controlling the workflow and
    executing the imported classes and functions as required.
    """

    # Define constants for scraping
    CRAG_URL = "https://27crags.com/crags/inia-droushia/"
    HEADERS = {
        'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
                AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}

    # Define scope and credential constants for google sheets client
    SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive"
    ]
    CREDS_FILE = "creds.json"

    # Initialize a scraper instance and store data in an object
    scraper = Scraper(HEADERS)
    crag = Crag(CRAG_URL, scraper)
    print("Crag successfully scraped!\n")

    # Create an instance of GoogleSheetsClient
    gsc = GoogleSheetsClient(CREDS_FILE, SCOPE)

    # prepare data for google sheets
    print("Compiling data to write to google sheets ...\n")
    boulder_data, route_data, ascent_data = compile_data(crag)

    # write data to gsheet
    print("Writing data to google sheets ...\n")
    gsc.write_data_to_sheet('data', 'boulders', boulder_data)
    gsc.write_data_to_sheet('data', 'routes', route_data)
    gsc.write_data_to_sheet('data', 'ascents', ascent_data)


if __name__ == "__main__":
    main()
