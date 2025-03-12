"""
The Crag class with stored attributes on initialization and methods to
extract information regarding the boulders contained in the crag, by
initializing a Boulder instance for each boulder related to a Crag instance.
"""
from modules.rich_utils import console, progress
from modules.scraper import Scraper
from modules.boulder import Boulder
import time
import aiohttp
import asyncio


class Crag:
    """
    A class to represent a crag, which contains associated boulders and
    boulder routes.

    Attributes:
        crag_url (str): The base URL of the crag.
        base_url (str): The base URL of the website.
        scraper (Scraper): The scraper instance to handle HTTP requests and
                            HTML parsing.
        routelist_url (str): The full URL containing the route list.
        boulders (list): List of Boulder instances associated with the crag.
    """

    def __init__(self, crag_url: str, scraper: Scraper, live=None):
        """
        Initialize Crag class instance.

        Args:
            crag_url (str): The base URL of the crag.
            headers (dict): The HTTP headers to use for the requests.
            scraper (Scraper): The scraper instance to handle HTTP requests
                                and HTML parsing.
        """
        self.console = console
        self.crag_url = crag_url
        # get the base 27crags domain url for use later in url navigation
        self.base_url = self.crag_url.split(".com")[0] + ".com"
        self.scraper = scraper
        self.live = live
        # define full url containing routelist
        self.routelist_url = f"{self.crag_url}routelist"
        # call get_boulders method and pass boulders list as a crag attribute
        self.console.print(
            "Please wait while the scraper is retrieving info "
            f"from '{self.crag_url}' ...\n",
            style="bold yellow")
        self.boulders = [
        ]  # Initialize empty list, will be populated by get_boulders_async
        self.progress = progress

    def get_boulders(self, batch_size=3):
        """Get boulders in batches"""
        console.print(
            f'\nScraping boulder list from "{self.routelist_url} "'
            'crag...\n',
            style="bold yellow")

        # Get initial boulder list
        soup = self.scraper.get_html(self.routelist_url)
        # locate anchor elements with "sector-item" class.
        # These contain the boulder pages, exclude the first one which is a
        # combined list of all routes
        boulder_elements = soup.find_all('a', attrs={'class':
                                                     'sector-item'})[1:]
        total_boulders = len(boulder_elements)

        # Initialize progress tracking
        task = progress.add_task("[yellow]Scraping crag data...",
                                 total=total_boulders)
        # Initialize list to store Boulder instances
        boulders = []
        # Process boulders in batches
        for i in range(0, total_boulders, batch_size):
            batch = boulder_elements[i:i + batch_size]

            # Process batch
            for boulder_elem in batch:
                # Get the boulder name
                boulder_name = boulder_elem.find('div',
                                                 attrs={
                                                     'class': 'name'
                                                 }).text.strip()
                console.print(
                    f'\nProcessing boulder info for "{boulder_name}" ...\n',
                    style="bold yellow")
                # Get the full URL for the boulder page
                boulder_url = self.base_url + boulder_elem['href']
                # Create a Boulder instance for each boulder
                boulder = Boulder(boulder_name, boulder_url, self.base_url,
                                  self.scraper, self.live)
                # Add the Boulder instance to the list
                boulders.append(boulder)

            # Update progress after each batch
            progress.update(task,
                            completed=min(i + batch_size, total_boulders),
                            total=total_boulders)

            # Add a small delay between batches
            time.sleep(self.scraper.min_request_interval)

        # Return the list of Boulder instances
        return boulders

    async def get_boulders_async(self, session: aiohttp.ClientSession):
        """Get boulders asynchronously"""
        console.print(
            f'\nScraping boulder list from "{self.routelist_url} "'
            'crag...\n',
            style="bold yellow")

        soup = await self.scraper.get_html_async(self.routelist_url, session)
        boulder_elements = soup.find_all('a', attrs={'class':
                                                     'sector-item'})[1:]
        total_boulders = len(boulder_elements)

        # Create progress task in live context if available
        task_id = None
        if self.live:
            task_id = self.live.add_task("[yellow]Scraping crag data...",
                                         total=total_boulders)

        batch_size = 3
        for i in range(0, total_boulders, batch_size):
            batch = boulder_elements[i:i + batch_size]
            batch_tasks = []

            for boulder_elem in batch:
                boulder_name = boulder_elem.find('div',
                                                 attrs={
                                                     'class': 'name'
                                                 }).text.strip()
                boulder_url = self.base_url + boulder_elem['href']

                boulder = Boulder(boulder_name, boulder_url, self.base_url,
                                  self.scraper, self.live)
                self.boulders.append(boulder)
                batch_tasks.append(boulder.async_init(session))

            await asyncio.gather(*batch_tasks)

            if self.live and task_id is not None:
                self.live.update(task_id,
                                 completed=min(i + len(batch), total_boulders))

        return self.boulders
