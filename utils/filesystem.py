"""Module to provide utility functions for the file system"""

import os
import zipfile
import requests


def create_directory(path):
    """
    Creates a new directory at the specified path.

    Args:
        path (str): The path to the directory to be created.

    Raises:
        OSError: If an error occurs during directory creation.
    """
    try:
        os.makedirs(path)
        print(f"Directory '{path}' created successfully.")
    except FileExistsError:
        print(f"The directory '{path}' already exist.")


def download_and_unzip_file(zip_url, destination_path):
    """Download the zip file, and it will unzip the file in the destication path.

    Args:
    zip_url: The url where we donwload the zip file
    destination_path: The path where we unzip the file that was downloaded

    Returns:
    It is an empty method, it only creates the files that were unzipped to the destination_path
    """
    # Download the file
    response = requests.get(zip_url, timeout=5)
    if response.status_code == 200:
        # Define the local zip file path
        local_zip_path = os.path.join(destination_path, 'data.zip')

        # Write the downloaded content to a local file
        with open(local_zip_path, 'wb') as file:
            file.write(response.content)

        # Unzip the file
        with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
            zip_ref.extractall(destination_path)

        # Delete the zip file after extraction
        os.remove(local_zip_path)
    else:
        print(f"Failed to download file. Status code: {response.status_code}")


def read_file_to_list(file_name):
    """Reads a file and returns a list with each line as an element.

    Args:
        file_name: The name of the file to read.

    Returns:
        A list with the lines of the file.
    """

    lines_list = []
    with open(file_name, 'r', encoding="utf-8") as file:
        for line in file:
            # Remove newlines at the end of each line
            line_without_newline = line.rstrip()
            lines_list.append(line_without_newline)
    return lines_list


def ls_directory(directory):
    """Lists the files and subdirectories in a given directory.

    Args: directory: The path of the directory to list.

    Returns: A list of the names of the items in the directory.
    """
    try:
        files = os.listdir(directory)
        return files
    except FileNotFoundError:
        print(f"The directory '{directory}' does not exist.")
        return []
