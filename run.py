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
    boulder_data = pd.DataFrame([(b.name, b.url) for b in crag.boulders],
                                columns=["Boulder Name", "Boulder URL"])

    route_data = []
    ascent_data = []

    for boulder in crag.boulders:
        for route in boulder.routes:
            route_data.append(
                (route.name,
                 route.url,
                 route.grade,
                 route.ascents,
                 route.rating))
            for ascent in route.ascent_log:
                ascent_data.append(
                    (route.name,
                     ascent['climber_name'],
                     ascent['ascent_type'],
                     ascent['ascent_date'].strftime('%Y-%m-%d')))

    route_data = pd.DataFrame(
        route_data,
        columns=["Route Name", "Route URL", "Grade", "Ascents", "Rating"])
    ascent_data = pd.DataFrame(
        ascent_data,
        columns=["Route Name", "Climber Name", "Ascent Type", "Ascent Date"])

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
    print(f"Size of '{crag.crag_url}' crag: \
    {len(crag.boulders)}")

    # Create an instance of GoogleSheetsClient
    gsc = GoogleSheetsClient(CREDS_FILE, SCOPE)

    # prepare data for google sheets
    boulder_data, route_data, ascent_data = compile_data(crag)

    # write data to gsheet
    gsc.write_data_to_sheet('data', 'boulders', boulder_data)
    gsc.write_data_to_sheet('data', 'routes', route_data)
    gsc.write_data_to_sheet('data', 'ascents', ascent_data)


if __name__ == "__main__":
    main()
