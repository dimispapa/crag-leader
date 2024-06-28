"""
The main application file used to run the program.

Imports the necessary classes/functions from the helper .py files:
- gsheets.py
- scraper.py
"""

from scraper import Scraper, Crag
from gsheets import GoogleSheetsClient


def main():
    """
    The main application function controlling the workflow and
    executing the imported classes and functions as required.
    """

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

    # Initialize a scraper instance and store data in an object
    scraper = Scraper(HEADERS)
    inia_droushia_crag = Crag(CRAG_URL, scraper)
    print(f"Size of '{inia_droushia_crag.crag_url}' crag: \
        {len(inia_droushia_crag.boulders)}")

    # Create an instance of GoogleSheetsClient
    gsc = GoogleSheetsClient(CREDS_FILE, SCOPE)


if __name__ == "__main__":
    main()
