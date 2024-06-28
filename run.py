"""
The main application file used to run the program.

Imports the necessary classes/functions from the following modules:
- gsheets.py
- scraper.py
"""

import pandas as pd
from scraper import Scraper, Crag
from gsheets import GoogleSheetsClient

# GLOBAL CONSTANTS
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

# Create an instance of GoogleSheetsClient
GSC = GoogleSheetsClient(CREDS_FILE, SCOPE)


def compile_data(crag: Crag):
    """
    Compile data from a Crag instance into pandas DataFrames for boulders,
    routes, and ascents.

    Args:
        crag (Crag): An instance of the Crag class containing the scraped data.

    Returns:
        tuple: A tuple containing three pandas DataFrames:
                (boulder_data, route_data, ascent_data).
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


def scrape_data():
    """
    The main application function controlling the workflow and
    executing the imported classes and functions as required.
    """

    # Initialize a scraper instance and store data in an object
    scraper = Scraper(HEADERS)
    crag = Crag(CRAG_URL, scraper)
    print("Crag successfully scraped!\n")

    # prepare data for google sheets
    print("Compiling data to write to google sheets ...\n")
    boulder_data, route_data, ascent_data = compile_data(crag)

    # write data to gsheet
    print("Writing data to google sheets ...\n")
    GSC.write_data_to_sheet('data', 'boulders', boulder_data)
    GSC.write_data_to_sheet('data', 'routes', route_data)
    GSC.write_data_to_sheet('data', 'ascents', ascent_data)
    print("Finished writing data to google sheets ...\n")


def retrieve_data():
    """
    Retrieve existing data from Google Sheets and parse into dataframes.

    Returns:
        tuple: A tuple containing three pandas DataFrames:
                (boulder_data, route_data, ascent_data).
    """

    # Retrieve data from worksheets
    boulder_data = pd.DataFrame(
        GSC.get_sheet_data('data', 'boulders'))
    route_data = pd.DataFrame(
        GSC.get_sheet_data('data', 'routes'))
    ascent_data = pd.DataFrame(
        GSC.get_sheet_data('data', 'ascents'))

    print("Data retrieval from Google Sheets completed.\n")

    return boulder_data, route_data, ascent_data


def get_user_choice():
    """
    Prompt the user to choose whether to scrape new data or retrieve existing
    data.

    Returns:
        str: The user's choice ('scrape' or 'retrieve').
    """
    while True:
        # prompt user choice.
        # Case-insesitive and remove leading/trailing spaces
        choice = input(
            "Do you want to scrape the latest data from 27crags or retrieve"
            " existing data? \n(scrape/retrieve): \n"
        ).strip().lower()

        # validate user choice
        if choice in ['scrape', 'retrieve']:
            return choice
        print("Invalid choice. Please enter 'scrape' or 'retrieve'.\n")


def main():
    """
    The main application function, prompting the user,
    controlling the workflow and executing the imported
    methods and functions as required.
    """

    # Get user choice
    choice = get_user_choice()

    # if user choses to scrape, then call scrape_data function
    # and then retrieve_data to print to console
    if choice == 'scrape':
        scrape_data()
        boulder_data, route_data, ascent_data = retrieve_data()
        print("\nBoulder Data:\n", boulder_data)
        print("\nRoute Data:\n", route_data)
        print("\nAscent Data:\n", ascent_data)

    # if user chooses to retrieve, then call retrieve_data function
    # and simply retrieve the existing data on google drive
    elif choice == 'retrieve':
        boulder_data, route_data, ascent_data = retrieve_data()
        print("\nBoulder Data:\n", boulder_data)
        print("\nRoute Data:\n", route_data)
        print("\nAscent Data:\n", ascent_data)


if __name__ == "__main__":
    main()
