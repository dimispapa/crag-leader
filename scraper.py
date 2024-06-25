import requests
from bs4 import BeautifulSoup


class Crag:
    """
    A class to represent a crag, which contains associated boulders and boulder routes.

    Attributes:
        routelist_url (str): The full URL containing the route list.
        session (requests.Session): The requests session for making HTTP requests.
    """

    def __init__(self, crag_url, headers):
        """
        Inits Crag class instance.

        Args:
            crag_url (str): The base URL of the crag.
            headers (dict): The HTTP headers to use for the requests.
        """
        self.crag_url = crag_url
        self.headers = headers
        # define full url containing routelist
        self.routelist_url = f"{self.crag_url}routelist"
        # initialize request session object
        self.session = requests.Session()

    def get_boulders(self):
        # get response from url
        response = self.session.get(
            url=self.routelist_url, headers=self.headers)
        # parse response html content
        soup = BeautifulSoup(response.content, 'html5lib')
        # locate anchor elements with "sector-item" class.
        # These contain the boulder pages, exclude the first one which is a combined list of all routes
        boulder_elements = soup.find_all(
            'a', attrs={'class': 'sector-item'})[1:]

        return boulder_elements


class Boulder:
    """
    A class to represent a boulder.

    Attributes:
        name (str): The name of the boulder.
        url (str): The URL of the boulder page.
    """

    def __init__(self, name, url):
        """
        Inits Boulder class instance.

        Args:
            name (str): The name of the boulder.
            url (str): The URL of the boulder page.
        """
        self.name = name
        self.url = url

    def __repr__(self):
        return f"Boulder(name={self.name}, url={self.url})"


# testing
CRAG_URL = "https://27crags.com/crags/inia-droushia/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
inia_droushia_crag = Crag(CRAG_URL, HEADERS)
boulder_elements = inia_droushia_crag.get_boulders()
print(boulder_elements)
