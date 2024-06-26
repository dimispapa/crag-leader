import requests
from bs4 import BeautifulSoup


class Scraper:
    """
    A class to handle HTTP requests and HTML parsing.
    Contains a get method to retrieve a response on a given URL.

    Attributes:
        session (requests.Session): The requests session for making HTTP requests.
        headers (dict): The HTTP headers to use for the requests.
    """
    
    def __init__(self, headers):
        """
        Initialize Scraper class instance.

        Args:
            headers (dict): The HTTP headers to use for the requests.
        """
        self.headers = headers
        self.session = requests.Session()

    def get(self, url):
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
    
    def __init__(self, crag_url, scraper):
        """
        Initialize Crag class instance.

        Args:
            crag_url (str): The base URL of the crag.
            headers (dict): The HTTP headers to use for the requests.
        """
        self.crag_url = crag_url
        # get the base 27crags domain url for use later
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
            name = boulder_elem.find(
                'div', attrs={'class': 'name'}).text.strip()
            url = self.base_url + boulder_elem['href'] # concat the boulder url on the base url

            # contstruct Boulder object and add to boulders list
            boulder = Boulder(name, url, self.scraper)
            boulders.append(boulder)

        # return the boulders list
        return boulders


class Boulder:
    """
    A class to represent a boulder.

    Attributes:
        name (str): The name of the boulder.
        boulder_url (str): The URL of the boulder page.
    """
    
    def __init__(self, name, boulder_url, scraper):
        """
        Initialize Boulder class instance.

        Args:
            name (str): The name of the boulder.
            boulder_url (str): The URL of the boulder page.
        """
        self.name = name
        self.boulder_url = boulder_url
        self.scraper = scraper

    def __repr__(self):
        """
        Return a string representation of the Boulder instance.

        Returns:
            str: A string representation of the Boulder instance.
        """
        return f"Boulder(name={self.name}, boulder_url={self.boulder_url})"

    def get_routes(self):
        """
        Retrieve the list of routes for the boulder.

        Returns:
            list: A list of Route instances.
        """
        
        # scrape parsed html content from url
        soup = self.scraper.get(self.boulder_url)
        
        # locate the table with class “route-list”
        routes_table = soup.find('table', attrs={'class':'route-list'})
        
        return routes_table

class Route:
    """
    A class to represent a boulder route.

    Attributes:
        name (str): The name of the route.
        url (str): The URL of the route page.
    """

    def __init__(self, name, url):
        """
        Initialize Route class instance.

        Args:
            name (str): The name of the route.
            url (str): The URL of the route page.
        """
        self.name = name
        self.url = url


# testing
CRAG_URL = "https://27crags.com/crags/inia-droushia/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
scraper = Scraper(HEADERS)
inia_droushia_crag = Crag(CRAG_URL, scraper)
print(inia_droushia_crag.boulders)
routes = inia_droushia_crag.boulders[0].get_routes()
print(routes.prettify())
