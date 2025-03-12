"""
The Scraper class with methods for the purpose of scraping and returning a
parsed HTML BeautifulSoup object with information ready to be extracted.

User is advised to import the 'Scraper' and 'Crag' classes in this order
to pass the Scraper instance as an argument for the Crag instance.
"""
import json
import requests
from bs4 import BeautifulSoup
import time
import os


class Scraper:
    """
    A class to handle HTTP requests and HTML parsing.
    Contains a get method to retrieve a response on a given URL.

    Attributes:
        session (requests.Session): The requests session for making HTTP
        requests.
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
        self.last_request_time = 0
        self.min_request_interval = int(
            os.environ.get("MIN_REQUEST_INTERVAL", 1))

    def _rate_limit(self):
        """
        Ensures requests are spaced out by at least min_request_interval seconds.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def get_html(self, url: str):
        """
        Make an HTTP GET request to the HTML from the specified URL.

        Args:
            url (str): The URL to make the request to.

        Returns:
            BeautifulSoup: The parsed HTML content of the response.
        """
        self._rate_limit()  # Add rate limiting
        response = self.session.get(url, headers=self.headers)
        return BeautifulSoup(response.content, 'html5lib')

    def get_json_html(self, url: str):
        """
        Make an HTTP GET request to the JSON file from the specified URL.
        Extract the HTML from JSON to parse the content.

        Args:
            url (str): The URL to make the request to.

        Returns:
            BeautifulSoup: The parsed HTML content of the response.
        """
        self._rate_limit()  # Add rate limiting
        response = self.session.get(url, headers=self.headers)
        # load the json
        additional_ascents_json = json.loads(response.text)
        # Convert the JSON content to HTML
        additional_ascents_html = additional_ascents_json['ticks']
        # return the parsed html content
        return BeautifulSoup(additional_ascents_html, 'html5lib')

    def login(self, username: str, password: str):
        """
        Login to 27crags.com using provided credentials.

        Args:
            username (str): 27crags.com username/email
            password (str): 27crags.com password

        Returns:
            bool: True if login successful, False otherwise
        """
        login_url = "https://27crags.com/site/login"

        # First get the login page to obtain any CSRF tokens
        self._rate_limit()  # Add rate limiting
        login_page = self.session.get(login_url, headers=self.headers)
        soup = BeautifulSoup(login_page.content, 'html5lib')

        # Find the CSRF token
        csrf_token = soup.find('input', {'name': '_csrf'}).get('value')

        # Prepare login data
        login_data = {
            '_csrf': csrf_token,
            'LoginForm[username]': username,
            'LoginForm[password]': password,
            'LoginForm[rememberMe]': '1'
        }

        # Perform login
        self._rate_limit()  # Add rate limiting
        response = self.session.post(login_url,
                                     data=login_data,
                                     headers=self.headers)

        return "dashboard" in response.url
