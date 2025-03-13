"""
Worker process for handling data scraping in the background.
This process is designed to run on a Heroku worker dyno.
"""
import asyncio
import time
import re
import os
import json
from datetime import datetime
import aiohttp
from modules.gsheets import GoogleSheetsClient
from modules.helper import scrape_data
from modules.rich_utils import console
from modules.scraper import Scraper

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


async def check_for_updates(scraper, session):
    """Check if there are new routes or ascents on the crag page"""
    console.print("Checking for updates on the crag page...",
                  style="bold blue")

    html = await scraper.get_html_async(CRAG_URL, session)

    # Look for updates in the feed items
    # We're looking for items with titles containing keywords
    feed_items = \
        re.findall(r'<div class="title"><span>(.*?)<\/span>', str(html)) + \
        re.findall(r'<div class="title">(.*?)<\/div>', str(html))

    # Keywords that indicate new content
    update_keywords = ["new route", "tick list"]

    # Check if any feed item contains our keywords
    has_updates = False
    update_items = []

    for item in feed_items:
        for keyword in update_keywords:
            if keyword.lower() in item.lower():
                has_updates = True
                update_items.append(item)
                break

    if has_updates:
        console.print(f"Found updates: {', '.join(update_items[:3])}",
                      style="bold green")
        return True, update_items
    else:
        console.print("No new updates found", style="yellow")
        return False, []


async def worker_process():
    """Main worker process that checks for updates
    and runs scraping if needed"""
    console.print("Worker started, checking for updates...",
                  style="bold green")

    # Create Google Sheets client
    gsc = GoogleSheetsClient(CREDS_JSON, SCOPE)

    # Create scraper instance
    scraper = Scraper(HEADERS)

    try:
        # Create a new client session
        async with aiohttp.ClientSession() as session:
            # Check for updates
            updates_found, update_items = await check_for_updates(
                scraper, session)

            # Get last scrape time from config
            last_scrape, duration = gsc.get_timestamp_duration('data')
            console.print(
                f"Last scrape was on: {last_scrape}"
                f" and took ~{duration} minutes",
                style="bold blue")

            # If updates were found or it's been too long since last scrape
            if updates_found:
                # Start time tracking
                start_time = time.time()

                # Store the update reason
                gsc.update_scrape_reason(
                    'data', f"Updates: {', '.join(update_items[:2])}")

                # Run the scraping process
                console.print("Starting scrape due to detected updates...",
                              style="bold green")
                boulder_data, route_data, ascent_data = await scrape_data(
                    HEADERS, CRAG_URL, gsc, session)

                # Calculate duration
                duration_secs = time.time() - start_time

                # Update timestamp with duration
                gsc.update_timestamp('data', duration_secs)

                # Also update the last scrape time in new format
                gsc.update_last_scrape_time(
                    'data',
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                # Log completion
                if boulder_data:
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
    asyncio.run(worker_process())
