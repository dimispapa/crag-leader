"""
The Boulder class with stored attributes on initialization and methods to
extract information regarding the routes contained in a boulder, by
initializing a Route instance for each route related to a Boulder instance.
"""
from modules.rich_utils import console, progress
from modules.scraper import Scraper
from modules.route import Route
import time
from modules.loggers import logger
import aiohttp
import asyncio


class Boulder:
    """
    A class to represent a boulder.

    Attributes:
        name (str): The name of the boulder.
        boulder_url (str): The URL of the boulder page.
        base_url (str): The base URL of the website.
        scraper (Scraper): The scraper instance to handle HTTP requests and
                            HTML parsing.
        routes (list): List of Routes instances associated with the
                        boulder.
    """

    def __init__(self,
                 name: str,
                 url: str,
                 base_url: str,
                 scraper: Scraper,
                 live=None):
        """
        Initialize Boulder class instance.

        Args:
            name (str): The name of the boulder.
            boulder_url (str): The URL of the boulder page.
            base_url (str): The base URL of the website.
            scraper (Scraper): The scraper instance to handle HTTP requests
                                and HTML parsing.
            routes (list): List of Routes instances associated with the
                            boulder.
        """
        self.name = name
        self.url = url
        self.base_url = base_url
        self.scraper = scraper
        self.live = live
        self.routes = []

    async def async_init(self, session: aiohttp.ClientSession):
        """Initialize routes asynchronously"""
        self.routes = await self.get_routes_async(session)
        return self

    async def get_routes_async(self, session: aiohttp.ClientSession):
        """Get routes asynchronously"""
        console.print(f'\nExtracting routes for "{self.name}"...\n',
                      style="bold yellow")

        soup = await self.scraper.get_html_async(self.url, session)
        routes_table_tbody = soup.find('tbody')
        routes = []

        if routes_table_tbody:
            tr_elements = routes_table_tbody.find_all('tr')

            # Create task for this boulder's routes
            task_id = progress.add_task(
                f"[cyan]Processing routes for {self.name}...",
                total=len(tr_elements))

            batch_size = 3
            processed_count = 0  # Track how many routes we've processed

            for i in range(0, len(tr_elements), batch_size):
                batch = tr_elements[i:i + batch_size]

                for tr_element in batch:
                    route = await self._process_route_element(
                        tr_element, session)
                    if route:
                        routes.append(route)
                    # Increment counter for each processed route
                    processed_count += 1
                    # Update progress after each route
                    progress.update(task_id, completed=processed_count)

                # Optional: Add a small delay between batches if needed
                await asyncio.sleep(0.1)

        return routes

    async def _process_route_element(self, tr_element, session):
        """Process a single route element"""
        try:
            anchor = tr_element.find('a')
            route_name = anchor.text.strip()
            route_url = self.base_url + anchor['href']
            grade = tr_element.find('span', attrs={
                'class': 'grade'
            }).text.strip().upper()
            td_elements = tr_element.find_all('td')
            no_of_ascents = td_elements[3].text.strip()
            rating = tr_element.find('div', attrs={
                'class': 'rating'
            }).text.strip()

            return Route(route_name, route_url, self.base_url, grade,
                         int(no_of_ascents), float(rating), self.scraper)
        except Exception as e:
            logger.error(f"Error processing route: {str(e)}")
            return None

    def __repr__(self):
        """
        Return a string representation of the Boulder instance.

        Returns:
            str: A string representation of the Boulder instance.
        """
        return f"Boulder(name={self.name}, url={self.url})"

    def get_routes(self, batch_size=3):
        """Retrieve the list of routes for the boulder in batches"""
        console.print(f'\n\tExtracting routes for "{self.name}"...\n',
                      style="bold yellow")

        soup = self.scraper.get_html(self.url)
        routes_table_tbody = soup.find('tbody')
        routes = []

        if routes_table_tbody:
            # find the tr elements
            tr_elements = routes_table_tbody.find_all('tr')

            # process routes in batches
            for i in range(0, len(tr_elements), batch_size):
                batch = tr_elements[i:i + batch_size]

                # process each route in the batch
                for tr_element in batch:
                    anchor = tr_element.find('a')
                    # get the route name
                    route_name = anchor.text.strip()
                    console.print(
                        f'\n\tExtracting info for route: "{route_name}"...',
                        style="bold yellow")
                    # get the route url
                    route_url = self.base_url + anchor['href']
                    # get the grade
                    grade = tr_element.find('span', attrs={
                        'class': 'grade'
                    }).text.strip().upper()
                    # get the number of ascents
                    td_elements = tr_element.find_all('td')
                    no_of_ascents = td_elements[3].text.strip()
                    # get the rating
                    rating = tr_element.find('div', attrs={
                        'class': 'rating'
                    }).text.strip()
                    # create a Route instance
                    route = Route(route_name, route_url, self.base_url, grade,
                                  int(no_of_ascents), float(rating),
                                  self.scraper)
                    # add the Route instance to the list
                    routes.append(route)

                # Add a small delay between batches
                time.sleep(self.scraper.min_request_interval)

        # return the list of Route instances
        return routes
