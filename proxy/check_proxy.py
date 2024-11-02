"""Module providing functions to scrape ip proxies."""

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup


def scrape_free_proxy(url, delay_min=1, delay_max=5, user_agent_list=None):
    """
    Scrapes free proxies from a website and filters them using is_working_proxy.

    Args:
        url (str): The URL of the website containing free proxies.
        delay_min (int, optional): Minimum delay between requests in seconds. Defaults to 1.
        delay_max (int, optional): Maximum delay between requests in seconds. Defaults to 5.
        user_agent_list (list, optional): A list of user agents to rotate for each request. 
        Defaults to None.
    Returns:s
        None
    """
    headers = {}

    if user_agent_list:
        headers['User-Agent'] = random.choice(user_agent_list)

    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()  # Raise an exception for non-200 status codes

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'table table-striped table-bordered'})

        if not table:
            logging.info("No table found with class 'table table-striped table-bordered' on %s"
                         , url)

        proxy_list = []
        for row in table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                ip_address = cells[0].text.strip()
                port = cells[1].text.strip()
                ip_proxy_address = ip_address + ':' + port
                proxy_list.append(ip_proxy_address)

        process_proxies(proxy_list, delay_min, delay_max)

    except requests.exceptions.RequestException as e:
        logging.error("Error accessing page: %s", e)


def is_working_proxy(ip_proxy_address):
    """
    Checks if a given proxy address is valid by making a request to a test URL.

    Args:
        ip_proxy_address (str): The IP proxy address with port to test.

    Returns:
        bool: True if the proxy is valid, False otherwise.
    """

    is_valid = False
    try:
        proxies = {"http": ip_proxy_address, "https": ip_proxy_address}
        res = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=5)  # Set a timeout
        if res.status_code == 200:
            is_valid = True
    except requests.exceptions.RequestException as e:
        logging.error("Error testing proxy address: %s", e)

    return is_valid


def validate_and_collect_proxy(proxy_address, valid_proxies, delay_min, delay_max):
    """
    Validates a given proxy address and adds it to a list of valid proxies if it passes the test.
    Introduces a random delay between checks to avoid overwhelming the target server.

    Args:
        proxy_address (str): The IP proxy address with port (e.g., "127.0.0.1:8080").
        valid_proxies (list): A list to store valid proxy addresses. Modified in-place.
        delay_min (int, optional): Minimum delay between requests in seconds. Defaults to 1.
        delay_max (int, optional): Maximum delay between requests in seconds. Defaults to 5.

    Returns:
        None
    """
    if is_working_proxy(proxy_address):
        valid_proxies.append(proxy_address)
        logging.info("Valid IP Proxy Address: %s", proxy_address)
        time.sleep(random.uniform(delay_min, delay_max))  # Introduce random delay
    else:
        logging.info("Invalid IP Proxy Address: %s", proxy_address)


def process_proxies(proxy_list, delay_min, delay_max):
    """
    Efficiently processes a list of proxy addresses, concurrently validating and collecting valid 
    ones.

    This function utilizes Python's `concurrent.futures.ThreadPoolExecutor` to execute the 
    validation tasks in parallel, improving performance. It also introduces a random delay 
    between checks to prevent overwhelming the target server.

    Args:
        proxy_list (list): A list of proxy addresses (e.g., ["127.0.0.1:8080", "8.8.8.8:53"]).
        delay_min (int, optional): Minimum delay between requests in seconds. Defaults to 1.
        delay_max (int, optional): Maximum delay between requests in seconds. Defaults to 5.

    Returns:
        None

    Raises:
        concurrent.futures.exceptions.ExecutionError: If any exceptions occur during validation 
        in the threads.
    """

    valid_proxies = []

    # Use ThreadPoolExecutor to process proxies concurrently
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(validate_and_collect_proxy, proxy, valid_proxies, delay_min, delay_max)
            for proxy in proxy_list
        ]
        # Wait for all threads to complete
        for future in futures:
            future.result()  # This will raise exceptions if any occurred in threads

    # Write all valid proxies to file at once
    with open('./proxy/proxy_list.txt', 'w', encoding="utf-8") as file:
        for proxy in valid_proxies:
            file.write(proxy + "\n")

    logging.info("proxy_list.txt file created successfully")
