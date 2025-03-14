"""
Module contains helper functions used in other modules.
"""
import os
import pandas as pd
from gspread import WorksheetNotFound, SpreadsheetNotFound, client
from pyfiglet import figlet_format
from modules.scraper import Scraper
from modules.crag import Crag
from modules.rich_utils import console
from typing import Union
import asyncio
import aiohttp
import logging
from modules.rich_utils import live
import time

logger = logging.getLogger(__name__)


def clear():
    """
    Clear function to clean-up the terminal so things don't get messy.
    """
    os.system("cls" if os.name == "nt" else "clear")
    console.clear()


def rank_leaderboard(leaderboard: Union[pd.DataFrame, pd.Series],
                     ranking_column: str):
    """
    Sort and rank the leaderboard based on the selected column.

    Args:
        leaderboard (pandas.DataFrame): The leaderboard to be ranked.
        ranking_column (str): The column name to rank it by.

    Returns:
        pandas.DataFrame: The sorted and ranked leaderboard.
    """
    # apply rank() method to the leaderboard
    # if it's a dataframe
    if isinstance(leaderboard, pd.DataFrame):
        leaderboard['Rank'] = \
            leaderboard[ranking_column].rank(
                method='min', ascending=False).astype(int)
    # if it's a series
    elif isinstance(leaderboard, pd.Series):
        # Create a DataFrame from the Series
        leaderboard = leaderboard.to_frame()
        leaderboard['Rank'] = \
            leaderboard.rank(method='min', ascending=False).astype(int)
    # sort the leaderboard by rank
    ranked_leaderboard = leaderboard.sort_values(by='Rank')

    return ranked_leaderboard


def welcome_msg():
    """
    Prints the welcome message and ASCII art to the console.
    """
    ascii_art = figlet_format("Crag Leader", font='doom')
    console.print(ascii_art, style="bold green")

    console.print(
        "Welcome to the CRAG LEADER application.\nA leaderboard "
        "designed for boulderers who log their ascents on 27crags, "
        "on the Inia & Droushia crag in Cyprus!"
        "\n",
        style="bold cyan")


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
    boulder_data = pd.DataFrame(
        [(b.name, b.url, [route.name for route in b.routes])
         for b in crag.boulders],
        columns=["Boulder Name", "Boulder URL", "Route List"])

    # Initialize lists to hold route and ascent data
    route_data = []
    ascent_data = []

    # Iterate through each boulder in the crag
    for boulder in crag.boulders:
        # Iterate through each route in the current boulder
        for route in boulder.routes:
            # Append route information to route_data list
            route_data.append((route.name, boulder.name, route.url,
                               route.grade, route.ascents, route.rating))
            # Iterate through each ascent log in the current route
            for ascent in route.ascent_log:
                # Append ascent information to ascent_data list
                ascent_data.append(
                    (route.name, route.grade, boulder.name,
                     ascent['climber_name'], ascent['ascent_type'],
                     ascent['ascent_date'].strftime('%Y-%m-%d')))

    # Create DataFrame for route data
    route_data = pd.DataFrame(route_data,
                              columns=[
                                  "Route Name", "Boulder Name", "Route URL",
                                  "Grade", "Ascents", "Rating"
                              ])

    # Create DataFrame for ascent data
    ascent_data = pd.DataFrame(ascent_data,
                               columns=[
                                   "Route Name", "Grade", "Boulder Name",
                                   "Climber Name", "Ascent Type", "Ascent Date"
                               ])

    return boulder_data, route_data, ascent_data


async def async_scrape_data(headers: dict,
                            crag_url: str,
                            gsc: client,
                            session=None):
    """
    Async version of scrape_data - supports worker dyno
    by accepting an optional session.

    Args:
        headers (dict): HTTP headers to use for requests
        crag_url (str): URL of the crag to scrape
        gsc (client): Google Sheets client
        session (aiohttp.ClientSession, optional): Existing client session
        to use

    Returns:
        tuple: (boulder_data, route_data, ascent_data) DataFrames
    """
    clear()
    scraper = Scraper(headers)

    # Fetch credentials from environment variables
    username = os.environ.get('27CRAGS_USERNAME')
    password = os.environ.get('27CRAGS_PASSWORD')
    useralias = os.environ.get('27CRAGS_USERALIAS')

    # Check if credentials are missing
    if not username or not password:
        console.print("\nMissing 27crags.com credentials.", style="bold red")
        return None, None, None  # Return immediately if credentials missing

    # Add debug logging
    logger.debug(f"Username present: {bool(username)}")
    logger.debug(f"Password present: {bool(password)}")
    logger.debug(f"Useralias present: {bool(useralias)}")

    # Attempt login
    if not scraper.login(username, password, useralias):
        console.print("\nFailed to login to 27crags.com.", style="bold red")
        return None, None, None

    logger.debug("Login successful, proceeding with scraping")

    # Start the live display
    live.start()

    # Track if we created our own session
    own_session = session is None

    # Create session if none was provided
    if own_session:
        session = aiohttp.ClientSession()

    start_time = time.time()

    try:
        # Create crag instance
        crag = Crag(crag_url, scraper)

        # Get boulders asynchronously
        await crag.get_boulders_async(session)

        # Compile data
        boulder_data, route_data, ascent_data = compile_data(crag)

        # Write to sheets
        clear()
        console.print("\nWriting data to google sheets ...\n",
                      style="bold yellow")
        gsc.write_data_to_sheet(
            'data',
            'boulders',
            boulder_data,
            # Save space by setting rows and cols to
            # the nearest multiple of 10
            rows=round(len(boulder_data) / 10) * 10,
            cols=round(len(boulder_data.columns) / 10) * 10)
        gsc.write_data_to_sheet(
            'data',
            'routes',
            route_data,
            # Save space by setting rows and cols to
            # the nearest multiple of 10
            rows=round(len(route_data) / 10) * 10,
            cols=round(len(route_data.columns) / 10) * 10)
        gsc.write_data_to_sheet(
            'data',
            'ascents',
            ascent_data,
            # Save space by setting rows and cols to
            # the nearest multiple of 10
            rows=round(len(ascent_data) / 10) * 10,
            cols=round(len(ascent_data.columns) / 10) * 10)

        duration_secs = time.time() - start_time

        gsc.update_timestamp('data', duration_secs)

        console.print(
            f"\nScraping completed in {duration_secs/60:.2f} "
            f"minutes.\n"
            f"Data retrieved: \n- {len(boulder_data)} Boulders"
            f"\n- {len(route_data)} Routes"
            f"\n- {len(ascent_data)} Ascents\n",
            style="bold green")

        return boulder_data, route_data, ascent_data

    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        console.print(f"\nError during scraping: {str(e)}", style="bold red")
        return None, None, None
    finally:
        # Stop the live display
        live.stop()

        # Only close the session if we created it
        if own_session and session:
            await session.close()


def scrape_data(headers: dict, crag_url: str, gsc: client):
    """Wrapper for async_scrape_data to run in synchronous context"""
    return asyncio.run(async_scrape_data(headers, crag_url, gsc))


def retrieve_data(gsc: client):
    """
    Retrieve existing data from Google Sheets and parse into dataframes.

    Returns:
        tuple: A tuple containing three pandas DataFrames:
                (boulder_data, route_data, ascent_data).
    """
    clear()
    console.print("\nRetrieving data...\n", style="bold yellow")
    # Retrieve data from worksheets
    try:
        boulder_data = pd.DataFrame(gsc.get_sheet_data('data', 'boulders'))
        route_data = pd.DataFrame(gsc.get_sheet_data('data', 'routes'))
        ascent_data = pd.DataFrame(gsc.get_sheet_data('data', 'ascents'))

        # cast the Grade col to string to ensure consistency when
        # working with grades later
        route_data['Grade'] = route_data['Grade'].astype('str')
        ascent_data['Grade'] = ascent_data['Grade'].astype('str')

    except WorksheetNotFound:
        clear()
        return console.print(
            'Error: The data does '
            'not exist. Please choose the "scrape" option to '
            'retrieve data from 27crags.\n',
            style="bold red")

    except SpreadsheetNotFound:
        clear()
        return console.print(
            'Error: The Google Sheet file '
            'does not exist, please create a Google sheet '
            'file with name "data" and then choose '
            'to "scrape".\n',
            style="bold red")
    clear()
    console.print("\nData retrieval completed.\n", style="bold green")

    return boulder_data, route_data, ascent_data
