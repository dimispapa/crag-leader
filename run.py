"""
The main application file used to run the program.

Imports the necessary classes/functions from the helper .py files:
- gsheets.py
- scraper.py
"""

from scraper import Scraper, Crag


def main():
    """
    The main application function controlling the workflow and
    executing the imported classes and functions as required.
    """
    CRAG_URL = "https://27crags.com/crags/inia-droushia/"
    HEADERS = {
        'User-Agent':
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
                AppleWebKit/537.36 \
                    (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
    scraper = Scraper(HEADERS)
    inia_droushia_crag = Crag(CRAG_URL, scraper)
    print(f"Size of '{inia_droushia_crag.crag_url}' crag: \
        {len(inia_droushia_crag.boulders)}")


if __name__ == "__main__":
    main()
