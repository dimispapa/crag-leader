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
        """
        login_url = "https://27crags.com/login"

        try:
            # First get the login page to obtain CSRF token
            self._rate_limit()
            login_page = self.session.get(login_url, headers=self.headers)

            if login_page.status_code != 200:
                print(
                    f"Failed to load login page. Status code: {login_page.status_code}"
                )
                return False

            soup = BeautifulSoup(login_page.content, 'html5lib')

            # Get CSRF token from meta tag
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if not csrf_meta:
                print("Could not find CSRF token")
                return False

            csrf_token = csrf_meta.get('content')

            # Prepare login data with correct field names
            login_data = {
                'authenticity_token': csrf_token,
                'web_user[username]': username,
                'web_user[password]': password,
                'web_user[remember_me]': '1'
            }

            # Add required headers
            enhanced_headers = {
                **self.headers, 'Accept':
                'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://27crags.com',
                'Referer': login_url,
                'X-CSRF-Token': csrf_token
            }

            # Perform login
            self._rate_limit()
            response = self.session.post(login_url,
                                         data=login_data,
                                         headers=enhanced_headers,
                                         allow_redirects=True)

            # Check if login was successful
            if "/dashboard" in response.url or "climbers/dashboard" in response.url:
                return True

            if "Invalid email or password" in response.text:
                print("Login failed: Invalid credentials")
            else:
                print("Login failed: Unknown reason")

            return False

        except Exception as e:
            print(f"Login error: {str(e)}")
            return False
