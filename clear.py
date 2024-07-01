"""
Module contains clear helper function to clear the CLI.
"""

import os


def clear():
    """
    Clear function to clean-up the terminal so things don't get messy.
    """
    os.system("cls" if os.name == "nt" else "clear")
