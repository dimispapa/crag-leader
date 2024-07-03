"""
Module contains helper functions used in other modules.
"""
import os
from pandas import DataFrame, Series
from modules.rich_utils import console


def clear():
    """
    Clear function to clean-up the terminal so things don't get messy.
    """
    os.system("cls" if os.name == "nt" else "clear")
    console.clear()


def rank_leaderboard(leaderboard: DataFrame or Series, ranking_column: str):
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
    if isinstance(leaderboard, DataFrame):
        leaderboard['Rank'] = \
            leaderboard[ranking_column].rank(
                method='min', ascending=False).astype(int)
    # if it's a series
    elif isinstance(leaderboard, Series):
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
    ascii_art = r"""
                _                 _     _
                | |               | |   | |
                | |__   ___  _   _| | __| | ___ _ __
                | '_ \ / _ \| | | | |/ _` |/ _ \ '__|
                | |_) | (_) | |_| | | (_| |  __/ |
                |_.__/ \___/ \__,_|_|\__,_|\___|_|
                """
    console.print(ascii_art, style="bold green")
    console.print("Welcome to the CRAG LEADER application.\nA leaderboard "
                  "designed for boulderers who log their ascents on 27crags, "
                  "on the Inia & Droushia crag in Cyprus!"
                  "\n", style="bold cyan")
