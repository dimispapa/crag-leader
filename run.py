"""
The main application file used to run the program.

Imports the necessary classes/functions from the following modules:
- gsheets.py
- scraper.py
"""
from time import sleep
import pandas as pd
from rich.prompt import Prompt
from gspread import exceptions
from modules.rich_utils import console, progress, display_table, show_help
from modules.gsheets import GoogleSheetsClient
from modules.score import ScoreCalculator
from modules.helper import (scrape_data, retrieve_data, clear, welcome_msg,
                            rank_leaderboard)

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


def leaderboard_mode(agg_table: pd.DataFrame,
                     calc_master_grade: ScoreCalculator.calc_master_grade):
    """
    Present the user with different leaderboard options and display the
    selected leaderboard.
    """
    # Dictionary to map user choices to leaderboard columns and
    # descriptions
    leaderboard_options = {
        '1': ('Total Score', 'Overall leaderboard - ranks climbers '
              'after summing up the Base Points based on grade (double '
              'points for flash), Volume Score and Unique Ascent Score.'),
        '2': ('Volume Score', 'Volume leaderboard - ranks climbers based '
              'on number of ascents counting 25 points every 5 ascents.'),
        '3': ('Unique Ascent Score', 'Unique Ascents leaderboard - ranks '
              'climbers by only counting unique ascents and awarding for'
              'double the normal base points for the grade.')
    }

    # keep looping until user decides to exit
    while True:
        # first clear the terminal from clutter
        clear()
        # Present the options to the user
        console.print("\nPlease choose a leaderboard to view or type "
                      "'help' for more information:",
                      style="bold cyan")
        console.print("1 - Total Score leaderboard", style="bold cyan")
        console.print("2 - Volume leaderboard", style="bold cyan")
        console.print("3 - Unique Ascents leaderboard", style="bold cyan")
        console.print("4 - Master Grade leaderboard", style="bold cyan")
        console.print("5 - Exit", style="bold cyan")

        choice = Prompt.ask("[bold cyan]Enter your choice (1-5)").strip()

        # if choice is 1, 2 or 3
        if choice in leaderboard_options:
            # Clear the terminal
            clear()
            # process the leaderboard
            lead_option, description = leaderboard_options[choice]
            leaderboard = rank_leaderboard(agg_table, lead_option)
            # display the leaderboard
            display_table(description, leaderboard)

        # Master Grade leaderboard
        elif choice == '4':
            # clear the terminal
            clear()
            # ask user to input a grade
            grade = Prompt.ask("[bold cyan]"
                               "Enter the grade (e.g., 3, 6A, 9A): "
                               ).strip().upper()
            # calc the master grade score
            grade_leaderboard = calc_master_grade(grade)

            # sort and rank the leaderboard
            grade_leaderboard = rank_leaderboard(
                grade_leaderboard[f'Num of {grade} Ascents'],
                f'Num of {grade} Ascents'
            )
            # display the leaderboard
            display_table(f"\nMaster Grade Leaderboard for {grade}",
                          leaderboard)

        # Exit the loop and leaderboard menu
        elif choice == '5':
            clear()
            console.print("\nExiting the leaderboard menu...\n",
                          style="bold red")
            # slight delay
            sleep(1)
            # clear terminal and run the main func again
            clear()
            main()
            # break the loop
            break

        # display help options
        elif choice == 'help':
            clear()
            show_help()

        # Invalidate choice
        else:
            clear()
            console.print(f"\nInvalid choice. You've entered '{choice}'."
                          " Please enter a number between 1 and 5, "
                          "or type 'help' for more info.\n",
                          style="bold red")

        # introduce slight delay to allow user to view output before
        # prompting again
        sleep(1)


def main():
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
            scrape_data(HEADERS, CRAG_URL, GSC)
        # retrieve data
        boulder_data, route_data, ascent_data = \
            retrieve_data(GSC)
        console.print(f"\nData retrieved: \n- {len(boulder_data)} Boulders"
                      f"\n- {len(route_data)} Routes"
                      f"\n- {len(ascent_data)} Ascents\n",
                      style="bold green")

    # if user chooses to retrieve, then call retrieve_data function
    # and simply retrieve the existing data on google drive
    elif choice == 'retrieve':
        boulder_data, route_data, ascent_data = \
            retrieve_data(GSC)
        console.print(f"\nData retrieved: \n- {len(boulder_data)} Boulders"
                      f"\n- {len(route_data)} Routes"
                      f"\n- {len(ascent_data)} Ascents\n",
                      style="bold green")

    # initialize the score calculator class and calculate scores
    console.print("\nCalculating scores ...\n", style="bold yellow")
    score_calculator = ScoreCalculator(GSC, ascent_data)
    aggregate_table = score_calculator.calculate_scores()
    console.print("\nScores have been calculated!\n", style="bold green")

    # prompt the user to choose the leaderboard
    # pass the calc_master_grade method of the score_calculator instance
    # to be used if the user chooses option 4
    leaderboard_mode(aggregate_table,
                     score_calculator.calc_master_grade)


try:
    if __name__ == "__main__":
        main()

except exceptions.APIError as e:
    console.print(
        f"APIError: {e}. Please try reloading the page and app.",
        style="bold red")
