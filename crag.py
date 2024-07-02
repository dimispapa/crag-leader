"""
The Crag class with stored attributes on initialization and methods to
extract information regarding the boulders contained in the crag, by
initializing a Boulder instance for each boulder related to a Crag instance.
"""
from scraper import Scraper
from boulder import Boulder


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

    def __init__(self, crag_url: str, scraper: Scraper):
        """
        Initialize Crag class instance.

        Args:
            crag_url (str): The base URL of the crag.
            headers (dict): The HTTP headers to use for the requests.
            scraper (Scraper): The scraper instance to handle HTTP requests
                                and HTML parsing.
        """
        self.crag_url = crag_url
        # get the base 27crags domain url for use later in url navigation
        self.base_url = self.crag_url.split(".com")[0] + ".com"
        self.scraper = scraper
        # define full url containing routelist
        self.routelist_url = f"{self.crag_url}routelist"
        # call get_boulders method and pass boulders list as a crag attribute
        print("Please wait while the scraper is retrieving info from "
              f"'{self.crag_url}' ...\n")
        self.boulders = self.get_boulders()

    def get_boulders(self):
        """
        Retrieve the list of boulders for the crag.

        Returns:
            list: A list of Boulder instances.
        """
        # scrape parsed html content from url
        print(f'Scraping boulder list from "{self.routelist_url}" crag...\n')
        soup = self.scraper.get_html(self.routelist_url)

        # locate anchor elements with "sector-item" class.
        # These contain the boulder pages, exclude the first one which is a
        # combined list of all routes
        boulder_elements = soup.find_all(
            'a', attrs={'class': 'sector-item'})[1:]

        boulders = []  # initialize empty boulders list

        # loop through the boulder elements to extract the boulder name
        # and url
        print("Extracting boulder info...\n")
        for boulder_elem in boulder_elements:
            # extract attributes from anchor element
            boulder_name = boulder_elem.find(
                'div', attrs={'class': 'name'}).text.strip()
            print(f'Processing boulder info for "{boulder_name}" ...\n')
            # concat the boulder url on the base url
            boulder_url = self.base_url + boulder_elem['href']

            # contstruct Boulder object and add to boulders list
            boulder = Boulder(boulder_name, boulder_url,
                              self.base_url, self.scraper)
            boulders.append(boulder)

        # return the boulders list
        return boulders
