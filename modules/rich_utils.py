"""
Initializes the console and progress objects from the rich library
in order to utilise in other modules as needed and avoid passing
around of attributes in classes.
"""

from rich.console import Console
from rich.progress import (Progress, SpinnerColumn, BarColumn, TextColumn,
                           TimeElapsedColumn, TimeRemainingColumn)
from rich.table import Table
from pandas import DataFrame
from rich.live import Live

# Initialize the Console
console = Console()

# Create a more informative progress bar
progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TimeElapsedColumn(),  # Shows time elapsed
    TimeRemainingColumn(),  # Shows estimated time remaining
    expand=True,
    console=console,  # Explicitly set console
    transient=True  # Make it transient so it stays in place
)


def display_progress_with_output():
    """Create a live display with fixed progress bar at bottom"""
    return Live(
        progress,
        console=console,
        refresh_per_second=10,
        transient=True,  # Keep progress bar transient
        auto_refresh=True,  # Enable auto-refresh
        vertical_overflow="visible"  # Allow content to scroll
    )


def display_table(title: str, leaderboard: DataFrame):
    """
    Display a leaderboard using a Rich table with the specified title.

    Args:
        title (str): The title or description of the table.
        leaderboard (pandas.DataFrame): The DataFrame containing the
                                        leaderboard data.
    """
    # add an empty line before
    console.print("\n")
    # create a table with title or description
    table = Table(title=title, show_lines=True)
    # add columns to the table
    table.add_column("Climber Name", justify="right")  # add index name
    for col in leaderboard.columns:
        table.add_column(col, justify="right")
    # add rows to the table
    for index, row in leaderboard.iterrows():
        table.add_row(str(index), *[str(value) for value in row])
    # display the leaderboard
    console.print(table)
    # add an empty line after
    console.print("\n")


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
