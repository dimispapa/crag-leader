"""
The Boulder class with stored attributes on initialization and methods to
extract information regarding the routes contained in a boulder, by
initializing a Route instance for each route related to a Boulder instance.
"""
from modules.rich_utils import console
from modules.scraper import Scraper
from modules.route import Route
import time


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

    def __init__(self, name: str, url: str, base_url: str, scraper: Scraper):
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
        # call get_routes method and pass routes list as a boulder attribute
        self.routes = self.get_routes()

    def __repr__(self):
        """
        Return a string representation of the Boulder instance.

        Returns:
            str: A string representation of the Boulder instance.
        """
        return f"Boulder(name={self.name}, url={self.url})"

    def get_routes(self, batch_size=3):
        """Retrieve the list of routes for the boulder in batches"""
        console.print(f'\nExtracting routes for "{self.name}"...\n',
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
                        f'\nExtracting route info for "{route_name}"...\n',
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
