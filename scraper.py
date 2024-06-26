import requests
from bs4 import BeautifulSoup
from datetime import datetime


class Scraper:
    """
    A class to handle HTTP requests and HTML parsing.
    Contains a get method to retrieve a response on a given URL.

    Attributes:
        session (requests.Session): The requests session for making HTTP requests.
        headers (dict): The HTTP headers to use for the requests.
    """

    def __init__(self, headers: dict):
        """
        Initialize Scraper class instance.

        Args:
            headers (dict): The HTTP headers to use for the requests.
        """
        self.headers = headers
        self.session = requests.Session()

    def get(self, url: str):
        """
        Make an HTTP GET request to the specified URL.

        Args:
            url (str): The URL to make the request to.

        Returns:
            BeautifulSoup: The parsed HTML content of the response.
        """
        response = self.session.get(url, headers=self.headers)
        return BeautifulSoup(response.content, 'html5lib')


class Crag:
    """
    A class to represent a crag, which contains associated boulders and boulder routes.

    Attributes:
        crag_url (str): The base URL of the crag.
        base_url (str): The base URL of the website.
        scraper (Scraper): The scraper instance to handle HTTP requests and HTML parsing.
        routelist_url (str): The full URL containing the route list.
        boulders (list): List of Boulder instances associated with the crag.
    """

    def __init__(self, crag_url: str, scraper: Scraper):
        """
        Initialize Crag class instance.

        Args:
            crag_url (str): The base URL of the crag.
            headers (dict): The HTTP headers to use for the requests.
            scraper (Scraper): The scraper instance to handle HTTP requests and HTML parsing.
        """
        self.crag_url = crag_url
        # get the base 27crags domain url for use later in url navigation
        self.base_url = self.crag_url.split(".com")[0] + ".com"
        self.scraper = scraper
        # define full url containing routelist
        self.routelist_url = f"{self.crag_url}routelist"
        # call get_boulders method and pass boulders list as a crag attribute
        self.boulders = self.get_boulders()

    def get_boulders(self):
        """
        Retrieve the list of boulders for the crag.

        Returns:
            list: A list of Boulder instances.
        """
        # scrape parsed html content from url
        soup = self.scraper.get(self.routelist_url)

        # locate anchor elements with "sector-item" class.
        # These contain the boulder pages, exclude the first one which is a combined list of all routes
        boulder_elements = soup.find_all(
            'a', attrs={'class': 'sector-item'})[1:]

        boulders = []  # initialize empty boulders list

        # loop through the boulder elements and extract the boulder name and url
        for boulder_elem in boulder_elements:
            # extract attributes from anchor element
            boulder_name = boulder_elem.find(
                'div', attrs={'class': 'name'}).text.strip()
            # concat the boulder url on the base url
            boulder_url = self.base_url + boulder_elem['href']

            # contstruct Boulder object and add to boulders list
            boulder = Boulder(boulder_name, boulder_url,
                              self.base_url, self.scraper)
            boulders.append(boulder)

        # return the boulders list
        return boulders


class Boulder:
    """
    A class to represent a boulder.

    Attributes:
        name (str): The name of the boulder.
        boulder_url (str): The URL of the boulder page.
        base_url (str): The base URL of the website.
        scraper (Scraper): The scraper instance to handle HTTP requests and HTML parsing.
    """

    def __init__(self, name: str, url: str, base_url: str, scraper: Scraper):
        """
        Initialize Boulder class instance.

        Args:
            name (str): The name of the boulder.
            boulder_url (str): The URL of the boulder page.
            scraper (Scraper): The scraper instance to handle HTTP requests and HTML parsing.
            routes (list): List of Routes instances associated with the boulder.
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
        soup = self.scraper.get(self.url)

        # locate the tbody of the table element and the tr elements
        routes_table_tbody = soup.find('tbody')

        routes = []  # initialize empty routes list

        # loop through the tbody rows
        for tr_element in routes_table_tbody.find_all('tr'):
            # get the anchor element in the tr and extract name and url
            anchor = tr_element.find('a')
            route_name = anchor.text.strip()
            # concat the route url on the base url
            route_url = self.base_url + anchor['href']

            # get the grade and ensure consistent uppercase format i.e. "6C" not "6c"
            grade = tr_element.find(
                'span', attrs={'class': 'grade'}).text.strip().upper()

            # get the td elements to target based on index those not differentiated otherwise
            td_elements = tr_element.find_all('td')
            # extract the number of ascents
            no_of_ascents = td_elements[3].text.strip()

            # get the rating
            rating = tr_element.find(
                'div', attrs={'class': 'rating'}).text.strip()

            # construct the Route object and add it to the routes list
            route = Route(route_name, route_url, grade,
                          int(no_of_ascents), float(rating), self.scraper)
            routes.append(route)

        return routes


class Route:
    """
    A class to represent a boulder route.

    Attributes:
        name (str): The name of the route.
        url (str): The URL of the route page.
        grade (str): The grade of the route.
        ascents (int): The number of ascents.
        rating (float): The rating of the route.
        ascent_log (list): A list of climbers who have ascended the route and associated info.
        scraper (Scraper): The scraper instance to handle HTTP requests and HTML parsing.
    """

    def __init__(self, name: str, url: str, grade: str, ascents: int, rating: float, scraper: Scraper):
        """
        Initialize Route class instance.

        Args:
            name (str): The name of the route.
            url (str): The URL of the route page.
            grade (str): The grade of the route.
            ascents (int): The number of ascents.
            rating (float): The rating of the route.
            ascent_log (list): A list of climbers who have ascended the route and associated info.
            scraper (Scraper): The scraper instance to handle HTTP requests and HTML parsing.
        """
        self.name = name
        self.url = url
        self.grade = grade
        self.ascents = ascents
        self.rating = rating
        self.scraper = scraper
        # call the get_ascent_log method and pass the returned list of dictionaries as an instance attribute
        self.ascent_log = self.get_ascent_log()

    def __repr__(self):
        """
        Return a string representation of the Route instance.

        Returns:
            str: A string representation of the Route instance.
        """
        return f"Route(name={self.name}, route_url={self.url}, grade={self.grade}, ascents={self.ascents}, rating={self.rating})"

    def get_ascent_log(self):
        """
        Retrieve the ascent log for the route.

        Returns:
            list: A list of dictionaries containing climber's name, ascent type and date.
        """

        # scrape parsed html content from url
        soup = self.scraper.get(self.url)
        # locate the log elements containing the ascents
        log_elements = soup.find_all('div', attrs={'class': 'result-row'})

        ascent_log = []  # initialise empty ascent log list

        # check if there are any logs
        if log_elements:

            # loop through the log elements and extract ascent data
            for log in log_elements:
                # get the climber's name
                climber = log.find(
                    'a', attrs={'class': 'action'}).text.strip()
                # get the ascent type and format string to be all lower no spaces
                ascent_type = log.find(
                    'span', attrs={'class': 'ascent-type'}).text.strip().lower().replace(' ', '')
                # get date of ascent and convert to datetime object
                date_container = log.find(
                    'div', attrs={'class': 'date'}).find_all(recursive=False)[-1]
                date_string = date_container.text.strip()
                date = datetime.strptime(date_string, '%Y-%m-%d').date()

                # form a dictionary and add to ascent_log list
                ascent_dict = {'climber_name': climber,
                               'ascent_type': ascent_type,
                               'ascent_date': date}
                ascent_log.append(ascent_dict)

        else:
            print(f'no logs for route: {self.name}')

        return ascent_log


# testing
CRAG_URL = "https://27crags.com/crags/inia-droushia/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
scraper = Scraper(HEADERS)
inia_droushia_crag = Crag(CRAG_URL, scraper)
# boulders = inia_droushia_crag.boulders

# all_routes = []
# for boulder in boulders:
#     all_routes.append(boulder.get_routes())

# all_routes_flat = [route for route_list in all_routes for route in route_list]

print(None)
