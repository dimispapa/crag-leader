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


def process_update_item(item, title_text, ago):
    """
    Process a feed item update and create a detailed update message.

    Args:
        item: BeautifulSoup element containing the feed item
        title_text: The extracted title text for this update
        ago: The 'ago' element containing timestamp

    Returns:
        str: Formatted update detail string
    """
    # Get the description if available
    desc_div = item.find('div', class_='description')
    desc_text = desc_div.get_text(strip=True) if desc_div else ""

    # Get the climber name
    climber = item.find('a', class_='climber-name')
    climber_name = climber.get_text(strip=True) if climber else "Unknown"
    ago_text = ago.get_text(strip=True)

    # Create and return the detailed update item
    update_detail = f"{climber_name} {title_text} {ago_text} - {desc_text}"

    # Debug: Print when a match is found
    console.print(f"\n[bold green]DEBUG: Found update: {update_detail}[/]")

    return update_detail


async def check_for_updates(scraper, session, last_scrape):
    """Check if there are new routes or ascents on the crag page"""
    console.print("Checking for updates on the crag page...",
                  style="bold blue")

    # html is already a BeautifulSoup object
    soup = await scraper.get_html_async(CRAG_URL, session)

    # Debug: Verify we can find the feed-items ul container
    feed_container = soup.find('ul', class_='feed-items')
    if not feed_container:
        console.print(
            "\n[bold red]DEBUG: Could not find feed-items container[/]")
        return False, []

    # Find all feed items
    feed_items = feed_container.find_all('li', class_='item')

    # Debug: Print number of items found
    console.print(
        f"\n[bold yellow]DEBUG: Found {len(feed_items)} feed items[/]")

    # Keywords that indicate new route or ascent
    update_keywords = ["new route", "tick list"]
    has_updates = False
    update_items = []

    for item in feed_items:
        # Check if items was updated after the last scrape
        ago = item.find('a', class_='ago')
        if not is_recent_update(ago, last_scrape):
            continue

        # Find the title div within item-details
        title_div = item.find('div', class_='title')
        if not title_div:
            continue

        # Check for tick list updates (in anchor text)
        tick_list_link = title_div.find('a')
        if tick_list_link and 'tick list' in tick_list_link.get_text(
                strip=True).lower():
            title_text = title_div.get_text(strip=True)  # Get full context
            console.print(f"\n[bold yellow]DEBUG: "
                          f"Found tick list update: {title_text}[/]")

            update_detail = process_update_item(item, title_text, ago)
            has_updates = True
            update_items.append(update_detail)
            # Continue as already found one of the keywords
            continue

        # Check for new route updates (in span)
        new_route_span = title_div.find('span')
        if new_route_span and 'new route' in new_route_span.get_text(
                strip=True).lower():
            title_text = new_route_span.get_text(strip=True)
            console.print(f"\n[bold yellow]DEBUG: "
                          f"Found new route update: {title_text}[/]")

            update_detail = process_update_item(item, title_text, ago)
            has_updates = True
            update_items.append(update_detail)
            # Continue as already found one of the keywords
            continue

    # If updates were found, return them and true to signal for scraping
    if has_updates:
        console.print(f"Found updates: {', '.join(update_items[:3])}",
                      style="bold green")
        # Parse the update items into a dataframe
        updates_df = pd.DataFrame(update_items, columns=['Update Items'])
        return True, updates_df
    else:
        console.print(f"\n[bold yellow]DEBUG: "
                      f"No matches found for keywords: {update_keywords}[/]")
        console.print("No new updates found", style="yellow")
        return False, []


async def worker_processor():
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

            # Get last scrape time from config
            last_scrape, duration = gsc.get_timestamp_and_duration('data')
            console.print(
                f"Last scrape was on: {last_scrape}"
                f" and took ~{duration} minutes",
                style="bold blue")

            # Check for updates
            updates_found, updates_df = await check_for_updates(
                scraper, session, last_scrape)

            # If updates were found or it's been too long since last scrape
            if updates_found:
                # Write the update items to the sheet
                gsc.write_data_to_sheet(
                    'data', f'updates_{datetime.now().strftime("%Y-%m-%d")}',
                    updates_df)

                # Start time tracking
                start_time = time.time()

                # Store the update reason
                gsc.update_scrape_reason('data',
                                         "New routes or ascents detected")

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
    asyncio.run(worker_processor())
