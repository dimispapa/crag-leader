"""
Initializes the console and progress objects from the rich library
in order to utilise in other modules as needed and avoid passing
around of attributes in classes.
"""

from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from pandas import DataFrame

# Initialize the Console object
console = Console()

# Initialize the Progress object
progress = Progress(transient=True)


def display_table(title: str, leaderboard: DataFrame):
    """
    Display a leaderboard using a Rich table with the specified title.

    Args:
        title (str): The title or description of the table.
        leaderboard (pandas.DataFrame): The DataFrame containing the
                                        leaderboard data.
    """
    # create a table with title or description
    table = Table(title=title)
    # add columns to the table
    for col in leaderboard.columns:
        table.add_column(col, justify="right")
    # add rows to the table
    for index, row in leaderboard.iterrows():
        table.add_row(str(index), *[str(value) for value in row])
    # display the leaderboard
    console.print(table)
