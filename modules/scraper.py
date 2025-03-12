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
from loggers import logger


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
        self.is_authenticated = False
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

    def check_auth(self):
        """Check if currently authenticated"""
        if not self.is_authenticated:
            return False

        # Make request to protected endpoint
        response = self.session.get(
            f"https://27crags.com/climbers/{self.useralias}",
            headers=self.headers)
        return response.status_code == 200

    def login(self, username: str, password: str, useralias: str):
        """Login to 27crags.com using provided credentials."""
        login_url = "https://27crags.com/login"
        self.useralias = useralias

        try:
            # First get the login page to obtain CSRF token
            logger.debug("Attempting to get login page")
            self._rate_limit()
            login_page = self.session.get(login_url, headers=self.headers)

            if login_page.status_code != 200:
                logger.error(
                    f"Failed to load login page. Status code: {login_page.status_code}"
                )
                return False

            soup = BeautifulSoup(login_page.content, 'html5lib')

            # Get CSRF token from meta tag
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if not csrf_meta:
                logger.error("Could not find CSRF token")
                return False

            csrf_token = csrf_meta.get('content')
            logger.debug(f"Got CSRF token: {csrf_token[:10]}...")

            # Prepare login data
            login_data = {
                'authenticity_token': csrf_token,
                'web_user[username]': username,
                'web_user[password]': password,
                'web_user[remember_me]': '1'
            }
            logger.debug("Prepared login data")

            # Add required headers
            enhanced_headers = {
                **self.headers, 'Accept':
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRF-Token': csrf_token
            }
            logger.debug("Enhanced headers prepared")

            # Perform login
            logger.debug("Attempting login request")
            self._rate_limit()
            response = self.session.post(login_url,
                                         data=login_data,
                                         headers=enhanced_headers,
                                         allow_redirects=True)

            logger.debug(f"Login response status: {response.status_code}")
            logger.debug(f"Login response URL: {response.url}")

            # Check if login was successful
            if "/dashboard" in response.url or "climbers/dashboard" in response.url:
                logger.info("Login successful")
                return True

            if "Invalid email or password" in response.text:
                logger.error("Login failed: Invalid credentials")
            else:
                logger.error(
                    f"Login failed: Unknown reason. Response URL: {response.url}"
                )

            return False

        except Exception as e:
            logger.exception(f"Login error: {str(e)}")
            return False

    def get_html(self, url: str):
        """Make authenticated request"""
        if not self.check_auth():
            raise Exception("Not authenticated")

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
