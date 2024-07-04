"""
The main application file used to run the program.

Imports the necessary classes/functions from the following modules:
- gsheets.py
- scraper.py
"""

import asyncio
import pandas as pd
from gspread import WorksheetNotFound, SpreadsheetNotFound, exceptions
from rich.prompt import Prompt
from modules.rich_utils import console, progress
from modules.scraper import Scraper
from modules.crag import Crag
from modules.gsheets import GoogleSheetsClient
from modules.score import ScoreCalculator
from modules.helper import clear, welcome_msg

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
                     route.grade,
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
                 "Grade",
                 "Boulder Name",
                 "Climber Name",
                 "Ascent Type",
                 "Ascent Date"])

    return boulder_data, route_data, ascent_data


async def scrape_data():
    """
    The main application function controlling the workflow and
    executing the imported classes and functions as required.
    """
    # Initialize a scraper instance and store data in an object
    scraper = Scraper(HEADERS)
    crag = Crag(CRAG_URL, scraper)
    console.print("\nCrag successfully scraped!\n", style="bold green")

    # prepare data for google sheets
    console.print("\nCompiling data to write to google sheets ...\n",
                  style="bold yellow")
    boulder_data, route_data, ascent_data = compile_data(crag)

    # write data to gsheet
    console.print("\nWriting data to google sheets ...\n", style="bold yellow")
    GSC.write_data_to_sheet('data', 'boulders', boulder_data)
    GSC.write_data_to_sheet('data', 'routes', route_data)
    GSC.write_data_to_sheet('data', 'ascents', ascent_data)
    GSC.update_timestamp('data')
    console.print("\nFinished writing data to google sheets ...\n",
                  style="bold green")


async def retrieve_data():
    """
    Retrieve existing data from Google Sheets and parse into dataframes.

    Returns:
        tuple: A tuple containing three pandas DataFrames:
                (boulder_data, route_data, ascent_data).
    """
    console.print("Retrieving data...\n", style="bold yellow")
    # Retrieve data from worksheets
    try:
        boulder_data = pd.DataFrame(
            GSC.get_sheet_data('data', 'boulders'))
        route_data = pd.DataFrame(
            GSC.get_sheet_data('data', 'routes'))
        ascent_data = pd.DataFrame(
            GSC.get_sheet_data('data', 'ascents'))

    except WorksheetNotFound:
        return console.print('Error: The data does '
                             'not exist. Please choose the "scrape" option to '
                             'retrieve data from 27crags.\n', style="bold red")

    except SpreadsheetNotFound:
        return console.print('Error: The Google Sheet file '
                             'does not exist, please create a Google sheet '
                             'file with name "data" and then choose '
                             'to "scrape".\n', style="bold red")

    console.print("\nData retrieval completed.\n", style="bold green")

    return boulder_data, route_data, ascent_data


def get_user_choice():
    """
    Prompt the user to choose whether to scrape new data or retrieve existing
    data.

    Returns:
        str: The user's choice ('scrape' or 'retrieve').
    """
    while True:
        # get the latest timestamp from google sheet file
        # and handle value error to process a new scrape
        try:
            timestamp = GSC.get_timestamp('data')
        except ValueError as ve:
            console.print(f"Error retrieving timestamp: {ve}\n"
                          "Processing a new scrape as default option ...\n",
                          style="bold red")
            return 'scrape'

        # prompt user choice.
        # Case-insesitive and remove leading/trailing spaces
        choice = Prompt.ask(
            f"[bold cyan]Crag data has been last updated on: {timestamp}.\n"
            "Do you want to scrape the latest data from 27crags or retrieve"
            " existing data? \n"
            "(Please type 1 for 'scraping latest data' or "
            "2 for 'retrieving current stored data, then press enter.'.)"
        ).strip().lower()

        # check if entry is empty (or spaces):
        if not choice:
            clear()
            console.print("\n Invalid choice. You did not enter a value.\n"
                          "(Please enter 1 for 'scraping latest data' or "
                          "2 for 'retrieving current stored data'.)\n",
                          style="bold red")

        # validate user choice
        elif choice not in ['1', '2']:
            clear()
            console.print(f"\nInvalid choice. You've entered '{choice}'. \n"
                          "(Please enter 1 for 'scraping latest data' or "
                          "2 for 'retrieving current stored data'.)\n",
                          style="bold red")
        else:
            return 'scrape' if choice == '1' else 'retrieve'


async def main():
    """
    The main application function, prompting the user,
    controlling the workflow and executing the imported
    methods and functions as required.
    """
    # begin by clearing the terminal to declutter
    clear()
    # Ensure all columns are shown next to each other when printing
    pd.set_option('display.max_columns', None)  # Show all columns
    # Set a large enough width to avoid line wrapping
    pd.set_option('display.width', 1000)
    # Justify column headers to the left
    # pd.set_option('display.colheader_justify', 'left')

    # welcome message
    welcome_msg()
    # Get user choice
    choice = get_user_choice()

    # if user choses to scrape, then call scrape_data function
    # and then retrieve_data to print to console
    if choice == 'scrape':
        # open the progress context manager to track scraping
        with progress:
            await scrape_data()
        # retrieve data
        boulder_data, route_data, ascent_data = \
            await retrieve_data()
        console.print(f"\nData retrieved: \n- {len(boulder_data)} Boulders"
                      f"\n- {len(route_data)} Routes"
                      f"\n- {len(ascent_data)} Ascents\n",
                      style="bold green")

    # if user chooses to retrieve, then call retrieve_data function
    # and simply retrieve the existing data on google drive
    elif choice == 'retrieve':
        boulder_data, route_data, ascent_data = \
            await retrieve_data()
        console.print(f"\nData retrieved: \n- {len(boulder_data)} Boulders"
                      f"\n- {len(route_data)} Routes"
                      f"\n- {len(ascent_data)} Ascents\n",
                      style="bold green")

    # initialize the score calculator class and calculate scores
    console.print("\nCalculating scores ...\n", style="bold yellow")
    score_calculator = ScoreCalculator(GSC, ascent_data)
    score_calculator.calculate_scores()
    console.print("\nScores have been calculated!\n", style="bold green")

    # prompt the user to choose the leaderboard
    # before printing to the terminal
    score_calculator.leaderboard_mode()

try:
    if __name__ == "__main__":
        asyncio.run(main())

except exceptions.APIError as e:
    console.print(
        f"APIError: {e}. Please try reloading the page and app.",
        style="bold red")
