"""
The Scraper class with methods for the purpose of scraping and returning a
parsed HTML BeautifulSoup object with information ready to be extracted.

User is advised to import the 'Scraper' and 'Crag' classes in this order
to pass the Scraper instance as an argument for the Crag instance.
"""
import json
import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from modules.loggers import logger
from rich.console import Console
import time
import os

console = Console()


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
        self.session = requests.Session()  # Initialize synchronous session
        self.is_authenticated = False
        self.last_request_time = 0
        self.login_url = "https://27crags.com/login"
        # Change to float for more precise intervals
        self.min_request_interval = float(os.getenv("MIN_REQUEST_INTERVAL"))
        self.max_retries = int(os.getenv("MAX_RETRIES"))
        self.retry_delay = int(os.getenv("RETRY_DELAY"))
        self._rate_limit_lock = asyncio.Lock()  # Add lock for rate limiting

    def _rate_limit(self):
        """
        Ensures requests are spaced out by at least
        min_request_interval seconds.
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def login(self, username: str, password: str, useralias: str):
        """Login to 27crags.com using provided credentials."""
        self.useralias = useralias

        try:
            # First get the login page to obtain CSRF token
            logger.debug("Attempting to get login page")
            self._rate_limit()

            try:
                login_page = self.session.get(self.login_url,
                                              headers=self.headers)
                logger.debug(
                    f"Login page response status: {login_page.status_code}")
                logger.debug(
                    f"Login page response headers: {login_page.headers}")
            except Exception as e:
                logger.error(f"Failed to get login page: {str(e)}")
                return False

            if login_page.status_code != 200:
                logger.error(
                    f"Failed to load login page. Status code: "
                    f"{login_page.status_code}")
                return False

            if not login_page.content:
                logger.error("Login page response content is empty")
                return False

            soup = BeautifulSoup(login_page.content, 'html5lib')
            if not soup:
                logger.error("Failed to parse login page content")
                return False

            # Get CSRF token from meta tag
            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if not csrf_meta:
                logger.error("Could not find CSRF token meta tag")
                return False

            csrf_token = csrf_meta.get('content')
            if not csrf_token:
                logger.error("CSRF token not found in meta tag")
                return False

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
                'text/html,application/xhtml+xml,application/xml;q=0.9,'
                '*/*;q=0.8',
                'Content-Type':
                'application/x-www-form-urlencoded',
                'X-CSRF-Token':
                csrf_token
            }
            logger.debug("Enhanced headers prepared")

            # Perform login
            logger.debug("Attempting login request")
            self._rate_limit()
            response = self.session.post(self.login_url,
                                         data=login_data,
                                         headers=enhanced_headers,
                                         allow_redirects=True)

            logger.debug(f"Login response status: {response.status_code}")
            logger.debug(f"Login response URL: {response.url}")

            # Check login success by looking
            # for logged-in indicators in the page
            soup = BeautifulSoup(response.content, 'html5lib')

            # Check multiple indicators of successful login
            is_logged_in = any([
                # Check for dashboard redirect to home page
                "/" in response.url,
                # Check for logged-in body class
                soup.find('body', class_='user-logged') is not None,
                # Check for user menu elements
                soup.find('div', class_='user-menu') is not None,
                # Check for logout link
                soup.find('a', href='/logout') is not None
            ])

            if is_logged_in:
                self.is_authenticated = True
                console.print("\nLogin to 27crags was successful!",
                              style="bold green")
                return True

            # If login failed, check for specific error message
            if "Invalid email or password" in response.text:
                console.print("\nLogin to 27crags failed: Invalid credentials",
                              style="bold red")
            else:
                console.print(
                    "\nLogin to 27crags failed: Could not verify "
                    "login success",
                    style="bold red")

            return False

        except Exception as e:
            console.print(f"\nLogin to 27crags failed: {str(e)}",
                          style="bold red")
            return False

    def get_html(self, url: str):
        """Make an HTTP GET request with retry logic."""
        max_retries = self.max_retries
        retry_delay = self.retry_delay

        for attempt in range(max_retries):
            try:
                self._rate_limit()

                if attempt > 0:
                    console.print(
                        f"\nRetry attempt {attempt} of {max_retries-1}...",
                        style="bold yellow")

                response = self.session.get(url, headers=self.headers)

                if response.status_code == 429:
                    wait_time = int(
                        response.headers.get('Retry-After', retry_delay))
                    console.print(
                        f"\nRate limit reached. Waiting {wait_time} "
                        "seconds...",
                        style="bold yellow")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status(
                )  # Raise exception for other error status codes
                return BeautifulSoup(response.content, 'html5lib')

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    console.print(
                        f"\nFailed to fetch data after {max_retries} "
                        "attempts.",
                        style="bold red")
                    raise Exception(f"Failed to fetch {url}: {str(e)}")

                console.print(
                    f"\nRequest failed. Retrying in {retry_delay} seconds...",
                    style="bold yellow")
                time.sleep(retry_delay)

        raise Exception(f"Failed to fetch {url} after {max_retries} attempts")

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

    def get_batch_html(self, urls: list, batch_size=3):
        """Process multiple URLs in batches with rate limiting"""
        # Initialize results list
        results = []

        # Process URLs in batches
        for i in range(0, len(urls), batch_size):
            chunk = urls[i:i + batch_size]
            chunk_results = []

            # Process each URL in the batch
            for url in chunk:
                try:
                    result = self.get_html(url)  # Use existing get_html method
                    chunk_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to fetch {url}: {str(e)}")
                    chunk_results.append(None)

            results.extend(chunk_results)
            time.sleep(self.min_request_interval)  # Rate limit between chunks

        return results

    async def _async_rate_limit(self):
        """Thread-safe async rate limiting"""
        async with self._rate_limit_lock:  # Use lock to ensure thread safety
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.min_request_interval:
                await asyncio.sleep(self.min_request_interval -
                                    time_since_last_request)
            self.last_request_time = time.time()

    async def get_html_async(self, url: str, session: aiohttp.ClientSession):
        """Async version of get_html with retry logic."""
        for attempt in range(self.max_retries):
            try:
                await self._async_rate_limit()  # Now thread-safe

                if attempt > 0:
                    console.print(
                        f"\nRetry attempt {attempt} of "
                        f"{self.max_retries-1}...",
                        style="bold yellow")

                async with session.get(url, headers=self.headers) as response:
                    if response.status == 429:
                        wait_time = int(
                            response.headers.get('Retry-After',
                                                 self.retry_delay))
                        console.print(
                            f"\nRate limit reached. Waiting {wait_time} "
                            "seconds...",
                            style="bold yellow")
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    content = await response.text()
                    return BeautifulSoup(content, 'html5lib')

            except Exception as e:
                if attempt == self.max_retries - 1:
                    console.print(
                        f"\nFailed to fetch data after {self.max_retries} "
                        "attempts.",
                        style="bold red")
                    raise Exception(f"Failed to fetch {url}: {str(e)}")

                console.print(
                    f"\nRequest failed. Retrying in {self.retry_delay} "
                    "seconds...",
                    style="bold yellow")
                await asyncio.sleep(self.retry_delay)

        raise Exception(
            f"Failed to fetch {url} after {self.max_retries} attempts")

    async def get_json_html_async(self, url: str,
                                  session: aiohttp.ClientSession):
        """Async version of get_json_html"""
        await self._async_rate_limit()
        async with session.get(url, headers=self.headers) as response:
            content = await response.text()
            additional_ascents_json = json.loads(content)
            additional_ascents_html = additional_ascents_json['ticks']
            return BeautifulSoup(additional_ascents_html, 'html5lib')
