"""Module to scrape data"""

from concurrent.futures import ThreadPoolExecutor
import itertools
import logging
import os
import random
import time
import requests
from bs4 import BeautifulSoup
from utils import filesystem


def scrape_country(url):
    """
    Scrapes country data from a given website URL, potentially utilizing proxies for resilience.

    This function retrieves a list of country URLs and their corresponding names from the specified 
    website. It then uses a thread pool to scrape country-specific data concurrently 
    (if `scrape_all_countries` is True), optionally utilizing proxies from a file.

    Args:
        url (str): The base URL of the website containing country data.

    Returns:
        None

    Raises:
        requests.exceptions.RequestException: If an error occurs during the HTTP request.
        OSError: If an error occurs while reading the proxy list.
    """
    response = requests.get(url, timeout=5)
    if response.status_code != 200:
        logging.error("Error accessing page: %s", response.status_code)
        return

    # Parse HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract country URLs and names
    country_links = [
        ("https://data.worldbank.org" + link['href'], link['href'].split('/')[2].split('?')[0])
        for link in soup.find_all("a", href=lambda href: href and href.startswith("/country/"))
    ]

    # Read proxies and set up rotation
    proxies = filesystem.read_file_to_list("./proxy/proxy_list.txt")
    proxy_pool = itertools.cycle(proxies)  # Create a proxy cycle

    # Use ThreadPoolExecutor for efficient threading
    with ThreadPoolExecutor() as executor:
        for country_url, country_name in country_links:  # Only first country if specified
            proxy = next(proxy_pool)  # Get the next proxy
            logging.info("Scraping data for %s at %s using proxy %s"
                         , country_name, country_url, proxy)
            executor.submit(scrape_country_csv_data, country_name, country_url, proxy)


def scrape_country_csv_data(country_name, country_url, ip_proxy_address, delay_min=1, delay_max=5):
    """
    Scrapes CSV data for a specific country from the provided URL, optionally using a proxy and 
    introducing random delays.

    This function retrieves a list of downloadable CSV files related to the given country and 
    downloads them to a dedicated directory.
    It utilizes a provided proxy address if available and introduces random delays between requests
    to avoid overwhelming the server.

    Args:
        country_name (str): The name of the country for which to scrape data.
        country_url (str): The URL of the webpage containing the country data.
        ip_proxy_address (str, optional): The IP address and port of a proxy to be used for the 
        request. Defaults to None (no proxy).
        delay_min (int, optional): Minimum delay between requests in seconds. Defaults to 1.
        delay_max (int, optional): Maximum delay between requests in seconds. Defaults to 5.

    Returns:
        None

    Raises:
        requests.exceptions.RequestException: If an error occurs during the HTTP request.
        ConnectionError: If a connection error occurs during download.
    """
    proxies = {"http": ip_proxy_address, "https": ip_proxy_address}
    response = requests.get(country_url, proxies=proxies, timeout=10)
    if response.status_code != 200:
        logging.error("Error accessing page for %s: %s: %s"
                      , country_name, country_url, response.status_code)
        return

    # Process the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find all CSV download URLs
    country_csv_zip_urls = [
        link['href'] for link in soup.find_all("a", href=True)
        if link['href'].startswith("https://api.worldbank.org/v2/en/country/")
            and link['href'].endswith("csv")
    ]

    # Prepare directory for downloads
    directory_name = os.path.join('./data', country_name)
    filesystem.create_directory(directory_name)

    # Download and unzip each CSV zip file
    for zip_url in country_csv_zip_urls:
        try:
            filesystem.download_and_unzip_file(zip_url, directory_name)
            logging.info("Successfully downloaded data for %s: %s", country_name, zip_url)
        except ConnectionError as e:
            logging.error("Failed to download data for %s from %s: %s", country_name, zip_url, e)

    time.sleep(random.uniform(delay_min, delay_max))  # Introduce random delay
