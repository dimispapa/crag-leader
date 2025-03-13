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
from playwright.async_api import async_playwright

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
        ago_text = ago_element.get_text(strip=True)
        ago_int = int(ago_text.split(" ")[0])
        ago_metric = ago_text.split(" ")[1]

        # Convert everything to minutes for easy comparison
        minutes_since_update = 0
        if ago_metric == "days":
            minutes_since_update = ago_int * 24 * 60
        elif ago_metric == "hours":
            minutes_since_update = ago_int * 60
        elif ago_metric == "minutes":
            minutes_since_update = ago_int
        else:
            console.print(f"Unknown ago metric: {ago_metric}",
                          style="bold red")
            return False

        # If no last scrape time, treat as new update
        if not last_scrape_time:
            return True

        # Convert last_scrape to datetime and compare
        try:
            last_scrape_dt = datetime.strptime(last_scrape_time,
                                               '%Y-%m-%d %H:%M:%S')
            minutes_since_scrape = int(
                (datetime.now() - last_scrape_dt).total_seconds() / 60)

            # Debug output
            console.print(
                f"\n[bold yellow]DEBUG: Update was {minutes_since_update} "
                f"minutes ago, last scrape was {minutes_since_scrape} "
                f"minutes ago[/]")

            return minutes_since_update < minutes_since_scrape

        except ValueError:
            console.print(
                f"Error parsing last scrape timestamp: {last_scrape_time}",
                style="bold red")
            # If we can't parse the timestamp, treat as new update to be safe
            return True

    except (ValueError, IndexError) as e:
        console.print(f"Error parsing ago text '{ago_text}': {str(e)}",
                      style="bold red")
        return False


async def process_update_item(item, title_text, ago_text):
    """
    Process a feed item update and create a detailed update message.

    Args:
        item: Playwright element containing the feed item
        title_text: The extracted title text for this update
        ago_text: The extracted ago text

    Returns:
        str: Formatted update detail string
    """
    # Get the description if available
    desc_element = await item.query_selector('div.description')
    desc_text = (await
                 desc_element.text_content()).strip() if desc_element else ""

    # Get the climber name
    climber = await item.query_selector('a.climber-name')
    climber_name = await climber.text_content() if climber else "Unknown"

    # Create and return the detailed update item
    update_detail = f"{climber_name} {title_text} {ago_text} - {desc_text}"

    # Debug: Print when a match is found
    console.print(f"\n[bold green]DEBUG: Found update: {update_detail}[/]")

    return update_detail


async def check_for_updates(last_scrape):
    """Check if there are new routes or ascents on the crag page"""
    console.print("Checking for updates on the crag page...",
                  style="bold blue")

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await page.goto(CRAG_URL)
            await page.wait_for_selector('ul.feed-items')

            feed_items = await page.query_selector_all('li.item')
            console.print(
                f"\n[bold yellow]DEBUG: Found {len(feed_items)} feed items[/]")

            has_updates = False
            update_items = []

            for item in feed_items:
                # Check timestamp
                ago_element = await item.query_selector('a.ago')
                if not ago_element:
                    continue

                ago_text = await ago_element.text_content()
                if not is_recent_update(ago_text, last_scrape):
                    continue

                # Find the title div
                title_div = await item.query_selector('div.title')
                if not title_div:
                    continue

                title_text = await title_div.text_content()
                # Debug output to see exact content
                console.print(f"\n[bold yellow]DEBUG: Title text content: "
                              f"'{title_text}'[/]")

                # Check for updates
                tick_list = 'tick list' in title_text.lower()
                new_route = 'new route' in title_text.lower()
                if tick_list or new_route:
                    update_detail = await process_update_item(
                        item, title_text, ago_text)
                    has_updates = True
                    update_items.append(update_detail)

            if has_updates:
                console.print(f"Found updates: {', '.join(update_items[:3])}",
                              style="bold green")
                updates_df = pd.DataFrame(update_items,
                                          columns=['Update Items'])
                return True, updates_df
            else:
                console.print("No new updates found", style="yellow")
                return False, []

        finally:
            await browser.close()


async def worker_processor():
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
        updates_found, updates_df = await check_for_updates(last_scrape)

        # If updates were found or it's been too long since last scrape
        if updates_found:
            # Write the update items to the sheet
            gsc.write_data_to_sheet(
                'data', f'updates_{datetime.now().strftime("%Y-%m-%d")}',
                updates_df)

            # Start time tracking
            start_time = time.time()

            # Store the update reason
            gsc.update_scrape_reason('data', "New routes or ascents detected")

            # Run the scraping process
            console.print("Starting scrape due to detected updates...",
                          style="bold green")
            boulder_data, route_data, ascent_data = await scrape_data(
                HEADERS, CRAG_URL, gsc)

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
    asyncio.run(worker_processor())
