"""
Initializes the console and progress objects from the rich library
in order to utilise in other modules as needed and avoid passing
around of attributes in classes.
"""

from rich.console import Console
from rich.progress import Progress

# Initialize the Console object
console = Console()

# Initialize the Progress object
progress = Progress(transient=True)
