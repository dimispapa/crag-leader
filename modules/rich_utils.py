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
    table.add_column("Climber Name", justify="right")  # add index name
    for col in leaderboard.columns:
        table.add_column(col, justify="right")
    # add rows to the table
    for index, row in leaderboard.iterrows():
        table.add_row(str(index), *[str(value) for value in row])
    # display the leaderboard
    console.print(table)


def show_help():
    """
    Display help information for the leaderboard options.
    """
    help_text = """
    Welcome to the CRAG LEADER leaderboard menu.
    Here are the available options:

    1 - Total Score leaderboard: Display the overall rankings including base
                                 points (double for flash), volume score and
                                 the unique ascent score all summed up.
    2 - Volume leaderboard: Display the ranking based on volume of ascents,
                            earning 25 points for every 5 climbs logged.
    3 - Unique Ascents leaderboard: Display the rankings for only unique
                                    ascents, earning double base points for
                                    the grade.
    4 - Master Grade leaderboard: Display rankings per the chosen grade.
    5 - Exit: Exit the menu back to the starting screen.

    Enter the number corresponding to the option you want to select.
    """
    console.print(help_text, style="bold cyan")
