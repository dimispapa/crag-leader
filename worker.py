"""
Worker process for handling long-running scraping tasks
"""
from modules.helper import scrape_data
from modules.gsheets import GoogleSheetsClient

# Define constants (same as in run.py)
CRAG_URL = "https://27crags.com/crags/inia-droushia/"
HEADERS = {
    'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
            AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
CREDS_FILE = "creds.json"


def worker_task():
    """Main worker function to handle scraping"""
    gsc = GoogleSheetsClient(CREDS_FILE, SCOPE)
    scrape_data(HEADERS, CRAG_URL, gsc)


if __name__ == "__main__":
    worker_task()
