"""
The Crag class with stored attributes on initialization and methods to
extract information regarding the boulders contained in the crag, by
initializing a Boulder instance for each boulder related to a Crag instance.
"""
from modules.rich_utils import console, progress
from modules.scraper import Scraper
from modules.boulder import Boulder


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
        self.console = console
        self.crag_url = crag_url
        # get the base 27crags domain url for use later in url navigation
        self.base_url = self.crag_url.split(".com")[0] + ".com"
        self.scraper = scraper
        # define full url containing routelist
        self.routelist_url = f"{self.crag_url}routelist"
        # call get_boulders method and pass boulders list as a crag attribute
        # console.clear()
        self.console.print("Please wait while the scraper is retrieving info "
                           f"from '{self.crag_url}' ...\n",
                           style="bold yellow")
        self.boulders = self.get_boulders()
        self.progress = progress

    def get_boulders(self):
        """
        Retrieve the list of boulders for the crag.

        Returns:
            list: A list of Boulder instances.
        """
        # scrape parsed html content from url
        # console.clear()
        console.print(f'\nScraping boulder list from "{self.routelist_url} "'
                      'crag...\n', style="bold yellow")
        soup = self.scraper.get_html(self.routelist_url)

        # locate anchor elements with "sector-item" class.
        # These contain the boulder pages, exclude the first one which is a
        # combined list of all routes
        boulder_elements = soup.find_all(
            'a', attrs={'class': 'sector-item'})[1:]

        boulders = []  # initialize empty boulders list

        # initiate the progress task object to keep track
        task = progress.add_task("[yellow]Scraping crag data...",
                                 total=len(boulder_elements))
        # loop through the boulder elements to extract the boulder name
        # and url
        for boulder_elem in boulder_elements:
            # extract attributes from anchor element
            boulder_name = boulder_elem.find(
                'div', attrs={'class': 'name'}).text.strip()
            # console.clear()
            console.print(
                f'\nProcessing boulder info for "{boulder_name}" ...\n',
                style="bold yellow")
            # concat the boulder url on the base url
            boulder_url = self.base_url + boulder_elem['href']

            # contstruct Boulder object and add to boulders list
            boulder = Boulder(boulder_name, boulder_url,
                              self.base_url, self.scraper)
            boulders.append(boulder)
            # update the task progress
            progress.update(task, advance=1)

        # return the boulders list
        return boulders
