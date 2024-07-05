"""
The Boulder class with stored attributes on initialization and methods to
extract information regarding the routes contained in a boulder, by
initializing a Route instance for each route related to a Boulder instance.
"""
from modules.rich_utils import console
from modules.scraper import Scraper
from modules.route import Route


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

    def get_routes(self):
        """
        Retrieve the list of routes for the boulder.

        Returns:
            list: A list of Route instances.
        """

        # scrape parsed html content from url
        soup = self.scraper.get_html(self.url)

        # locate the tbody of the table element and the tr elements
        routes_table_tbody = soup.find('tbody')

        routes = []  # initialize empty routes list

        # find the tr elements
        tr_elements = routes_table_tbody.find_all('tr')

        # loop through the tbody rows
        for tr_element in tr_elements:
            # get the anchor element in the tr and extract name and url
            anchor = tr_element.find('a')
            route_name = anchor.text.strip()
            console.clear()
            console.print(f'\nExtracting route info for "{route_name}"...\n',
                          style="bold yellow")
            # concat the route url on the base url
            route_url = self.base_url + anchor['href']

            # get the grade and ensure consistent uppercase format i.e. "6C"
            # not "6c"
            grade = tr_element.find(
                'span', attrs={'class': 'grade'}).text.strip().upper()

            # get the td elements to target based on index those not
            # differentiated otherwise
            td_elements = tr_element.find_all('td')
            # extract the number of ascents
            no_of_ascents = td_elements[3].text.strip()

            # get the rating
            rating = tr_element.find(
                'div', attrs={'class': 'rating'}).text.strip()

            # construct the Route object and add it to the routes list
            route = Route(route_name, route_url, self.base_url, grade,
                          int(no_of_ascents), float(rating), self.scraper)
            routes.append(route)

        return routes
