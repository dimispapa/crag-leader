"""
Worker process for handling data scraping in the background.
This process is designed to run on a Heroku worker dyno.
"""
import asyncio
import time
import os
import json
import pandas as pd
from datetime import datetime
from modules.gsheets import GoogleSheetsClient
from modules.helper import scrape_data
from modules.rich_utils import console
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Define constants for scraping
CRAG_URL = "https://27crags.com/crags/inia-droushia/"
HEADERS = {
    'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) \
            AppleWebKit/537.36 \
                (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}

# Define scope and credential constants for google sheets client
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]
# Get credentials from environment variable
CREDS_ENV = os.environ.get('CREDS')

if CREDS_ENV:
    # Parse the JSON string into a dictionary
    CREDS_JSON = json.loads(CREDS_ENV)

else:
    # Fallback to file-based credentials for local development
    CREDS_JSON = "creds.json"


def is_recent_update(ago_element, last_scrape_time: str) -> bool:
    """
    Check if an update is more recent than the last scrape.

    Args:
        ago_element: BeautifulSoup element containing the 'ago' timestamp
        last_scrape_time: Timestamp string of last scrape in format
        '%Y-%m-%d %H:%M:%S'

    Returns:
        bool: True if update is more recent than last scrape, False otherwise
    """
    if not ago_element:
        console.print("Could not find timestamp for item", style="bold red")
        return False

    try:
        ago_text = ago_element.text
        ago_int = int(ago_text.split(" ")[0])
        ago_unit = ago_text.split(" ")[1]

        # Convert everything to minutes for easy comparison
        minutes_since_update = 0
        if ago_unit in ["days", "day"]:
            minutes_since_update = ago_int * 24 * 60
        elif ago_unit in ["hours", "hour"]:
            minutes_since_update = ago_int * 60
        elif ago_unit in ["minutes", "minute"]:
            minutes_since_update = ago_int
        else:
            console.print(f"Unknown ago unit: {ago_unit}", style="bold red")
            return False

        # If no last scrape time, treat as new update
        if not last_scrape_time:
            return True

        # Convert last_scrape to datetime and compare
        try:
            last_scrape_dt = datetime.strptime(last_scrape_time,
                                               "%b %d %Y %H:%M:%S")

            minutes_since_scrape = int(
                (datetime.now() - last_scrape_dt).total_seconds() / 60)

            # Debug output
            console.print(
                f"\n[bold yellow]DEBUG: Update was {minutes_since_update} "
                f"minutes ago, last scrape was {minutes_since_scrape} "
                f"minutes ago[/]")

            # Return True if update is more recent than last scrape
            return minutes_since_update < minutes_since_scrape

        except ValueError:
            console.print(
                f"Error parsing last scrape timestamp: {last_scrape_time}."
                f"Treating as new update to be safe.",
                style="bold red")
            # If we can't parse the timestamp,
            # treat as new update to be safe
            return True

    except (ValueError, IndexError) as e:
        console.print(f"Error parsing ago text '{ago_text}': {str(e)}",
                      style="bold red")
        return False


def create_driver():
    """Create and configure Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")

    if 'DYNO' in os.environ:  # If running on Heroku
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        service = Service(os.environ.get("CHROMEDRIVER_PATH"))
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:  # Local development
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver


def check_for_updates(last_scrape):
    """Check if there are new routes or ascents on the crag page"""
    console.print("Checking for updates on the crag page...",
                  style="bold blue")

    driver = create_driver()

    try:
        driver.get(CRAG_URL)
        # Wait for feed-items to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.feed-items")))
        # Get all feed items
        feed_items = driver.find_elements(By.CSS_SELECTOR, "li.item")
        console.print(
            f"\n[bold yellow]DEBUG: Found {len(feed_items)} feed items[/]")

        has_updates = False
        update_items = []
        # Iterate through each feed item
        for item in feed_items:
            # Check timestamp
            ago_element = item.find_element(By.CSS_SELECTOR, "a.ago")
            ago_text = ago_element.text

            if not is_recent_update(ago_element, last_scrape):
                continue

            # Find the title div
            title_div = item.find_element(By.CSS_SELECTOR, "div.title")
            title_text = title_div.text

            # Debug output
            console.print(
                f"\n[bold yellow]DEBUG: Title text content: '{title_text}'[/]")

            # Check for new routes or ascents
            tick_list = 'tick list' in title_text.lower()
            new_route = 'new route' in title_text.lower()
            if tick_list or new_route:
                # Fetch the update details
                update_detail = fetch_update_details(item, title_text,
                                                     ago_text)
                has_updates = True
                # Add the update to the list
                update_items.append(update_detail)

        # If there are updates, print them and return as dataframe
        if has_updates:
            console.print(f"Found updates: {', '.join(update_items[:3])}",
                          style="bold green")
            updates_df = pd.DataFrame(update_items, columns=['Update Items'])
            return True, updates_df

        # If no updates, print message and return False
        else:
            console.print("No new updates found", style="yellow")
            return False, None

    finally:
        driver.quit()


def fetch_update_details(item, title_text, ago_text):
    """Process a single update item"""
    try:
        desc_element = item.find_element(By.CSS_SELECTOR, "div.description")
        desc_text = desc_element.text

        climber_element = item.find_element(By.CSS_SELECTOR, "a.climber-name")
        climber_name = climber_element.text

        update_detail = f"{climber_name} {title_text} {ago_text} - {desc_text}"
        console.print(f"Found update: {update_detail}", style="green")
        return update_detail

    except Exception as e:
        console.print(f"Error fetching update details: {e}", style="red")
        return f"Error fetching update details: {title_text}"


def main():
    """Main worker process that checks for updates
    and runs scraping if needed"""
    console.print("Worker started, checking for updates...",
                  style="bold green")

    # Create Google Sheets client
    gsc = GoogleSheetsClient(CREDS_JSON, SCOPE)

    try:
        # Get last scrape time from config
        last_scrape, duration = gsc.get_timestamp_and_duration('data')
        console.print(
            f"Last scrape was on: {last_scrape}"
            f" and took ~{duration} minutes",
            style="bold blue")

        # Check for updates
        has_updates, updates_df = check_for_updates(last_scrape)

        # If updates were found or it's been too long since last scrape
        if has_updates:
            # Write the update items to the sheet
            gsc.write_data_to_sheet(
                'data',
                f'updates_{datetime.now().strftime("%Y-%m-%d")}',
                updates_df,
                rows=round(len(updates_df) / 10) * 10,
                cols=round(len(updates_df.columns) / 10) * 10)

            # Start time tracking
            start_time = time.time()

            # Run the scraping process in a new event loop
            console.print("Starting scrape due to detected updates...",
                          style="bold green")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                boulder_data, route_data, ascent_data = \
                    loop.run_until_complete(
                        scrape_data(HEADERS, CRAG_URL, gsc))
            finally:
                loop.close()

            # Log completion
            if boulder_data:
                # Calculate duration
                duration_secs = time.time() - start_time
                # Store the update reason
                gsc.update_scrape_reason('data',
                                         "New routes or ascents detected")
                console.print(
                    f"\nScraping completed in {duration_secs/60:.2f} "
                    f"minutes.\n"
                    f"Data retrieved: \n- {len(boulder_data)} Boulders"
                    f"\n- {len(route_data)} Routes"
                    f"\n- {len(ascent_data)} Ascents\n",
                    style="bold green")
            else:
                console.print("Scraping failed or no data retrieved.",
                              style="bold red")
        else:
            console.print("No update needed at this time.", style="yellow")

    except Exception as e:
        console.print(f"Error in worker process: {str(e)}", style="bold red")


if __name__ == "__main__":
    main()
