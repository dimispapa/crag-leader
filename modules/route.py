"""
The Route class with stored attributes on initialization and methods to
extract information regarding the ascents logged relevant to a Route instance.
"""
from datetime import datetime
from bs4 import BeautifulSoup
from rich_utils import console
from modules.scraper import Scraper


class Route:
    """
    A class to represent a boulder route.

    Attributes:
        name (str): The name of the route.
        url (str): The URL of the route page.
        base_url (str): The base URL of the website.
        grade (str): The grade of the route.
        ascents (int): The number of ascents.
        rating (float): The rating of the route.
        ascent_log (list): A list of climbers who have ascended the route and
                            associated info.
        scraper (Scraper): The scraper instance to handle HTTP requests and
                            HTML parsing.
    """

    def __init__(self, name: str, url: str, base_url: str, grade: str,
                 ascents: int, rating: float, scraper: Scraper):
        """
        Initialize Route class instance.

        Args:
            name (str): The name of the route.
            url (str): The URL of the route page.
            base_url (str): The base URL of the website.
            grade (str): The grade of the route.
            ascents (int): The number of ascents.
            rating (float): The rating of the route.
            ascent_log (list): A list of climbers who have ascended the route
                                and associated info.
            scraper (Scraper): The scraper instance to handle HTTP requests
                                and HTML parsing.
        """
        self.name = name
        self.url = url
        self.base_url = base_url
        self.grade = grade
        self.ascents = ascents
        self.rating = rating
        self.scraper = scraper
        # call the get_ascent_log method and pass the returned list of
        # dictionaries as an instance attribute
        self.ascent_log = self.get_ascent_log()

    def __repr__(self):
        """
        Return a string representation of the Route instance.

        Returns:
            str: A string representation of the Route instance.
        """
        return (f"Route(name={self.name}, route_url={self.url}, "
                f"grade={self.grade}, ascents={self.ascents}, "
                f"rating={self.rating}")

    def get_ascent_log(self):
        """
        Retrieve the ascent log for the route, including additional ascents.

        Returns:
            list: A list of dictionaries containing climber's name, ascent
            type and date.
        """

        # Get the initial page and parse the HTML
        console.print(f'\nScraping ascent log info for "{self.name}" '
                      'route ...\n', style="bold yellow")
        soup = self.scraper.get_html(self.url)
        ascent_log = self.extract_ascent_log(soup)

        # Check for the "More ascents" button
        # and fetch additional ascents if available
        more_ascents_button = soup.find('div',
                                        class_='js-more ticks text-center')
        if more_ascents_button:
            # access the anchor element and get the href link
            # to fetch the file with the printed json file
            more_ascents_url = more_ascents_button.find('a')['href']
            if more_ascents_url:
                # get full URL for scraper to access
                full_more_ascents_url = self.base_url + more_ascents_url
                # scrape additional ascents
                console.print('\nScraping additional ascents from '
                              f'"{full_more_ascents_url}" ...\n',
                              style="bold yellow")
                # fetch the url page with the printed json
                more_ascents_soup = self.scraper.get_json_html(
                    full_more_ascents_url)
                # call method to extract the info from the parsed HTML
                additional_ascent_log = self.extract_ascent_log(
                    more_ascents_soup)
                # extend the ascent_log list with the additional ascents
                ascent_log.extend(additional_ascent_log)

        return ascent_log

    def extract_ascent_log(self, soup: BeautifulSoup):
        """
        Extract the climbing log from the provided BeautifulSoup object.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the HTML
                                    content.

        Returns:
            list: A list of dictionaries containing climber's name, ascent
                    type, and date.
        """
        # locate the log elements containing the ascents
        log_elements = soup.find_all('div', attrs={'class': 'result-row'})

        ascent_log = []  # initialise empty ascent log list

        # check if there are any logs
        if log_elements:
            # loop through the log elements and extract ascent data
            for log in log_elements:
                try:
                    # get the climber's name
                    climber = log.find(
                        'a', attrs={'class': 'action'}).text.strip()
                    console.print('\nProcessing ascent log '
                                  f'info of climber "{climber}" ...\n',
                                  style='bold yellow')
                    # get the ascent type and format string to be
                    # all lower no spaces
                    ascent_type = log.find(
                        'span',
                        attrs={'class': 'ascent-type'}
                    ).text.strip().lower().replace(' ', '')
                    # get date of ascent and convert to datetime object
                    date_container = log.find(
                        'div',
                        attrs={'class': 'date'}).find_all(recursive=False)[-1]
                    date_string = date_container.text.strip()
                    date = datetime.strptime(date_string, '%Y-%m-%d').date()

                    # form a dictionary and add to ascent_log list
                    ascent_dict = {'climber_name': climber,
                                   'ascent_type': ascent_type,
                                   'ascent_date': date}
                    ascent_log.append(ascent_dict)

                # Handle error if the item has no attribute ascent_type
                # i.e. it is a public to-do list item,
                # then continue to next item
                except AttributeError:
                    continue

        else:
            print(f'no logs for route: {self.name}')

        return ascent_log
