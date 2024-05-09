"""
Created on 2024-05-05

@author: wf
"""
import json
import urllib.parse

import requests
from tqdm import tqdm

from snapquery.snapquery_core import NamedQuery, NamedQueryList, NamedQueryManager


class QueryImport:
    """
    Import named queries from a given URL or file.
    """

    def __init__(self, nqm: NamedQueryManager = None):
        """
        Constructor

        Args:
            nqm (NamedQueryManager, optional): The NamedQueryManager to use for storing queries.
        """
        self.nqm = nqm
        pass

    def import_from_json_file(
        self, json_file: str, with_store: bool = False, show_progress: bool = False
    ) -> NamedQueryList:
        """
        Import named queries from a JSON file.

        Args:
            json_file (str): Path to the JSON file.
            with_store (bool): If True, store the results in the NamedQueryManager.
            show_progress (bool): If True, show a progress bar during the import.

        Returns:
            NamedQueryList: A NamedQueryList object containing the imported NamedQuery objects.
        """
        nq_list = NamedQueryList.load_from_json_file(json_file)
        iterable = (
            tqdm(nq_list.queries, desc="Importing Named Queries")
            if show_progress
            else nq_list.queries
        )

        for nq in iterable:
            if not nq.sparql and nq.url.startswith("https://w.wiki/"):
                nq.sparql = self.read_from_short_url(nq.url)

        if with_store and self.nqm:
            self.nqm.store_named_query_list(nq_list)

        return nq_list

    def read_from_short_url(self, short_url: str) -> str:
        """
        Read a query from a short URL.

        Args:
            short_url (str): The short URL from which to read the query.

        Returns:
            str: The SPARQL query extracted from the short URL.

        Raises:
            Exception: If there's an error fetching or processing the URL.
        """
        sparql_query = None
        try:
            # Follow the redirection
            response = requests.head(short_url, allow_redirects=True)
            redirected_url = response.url

            # Check if the URL has the correct format
            parsed_url = urllib.parse.urlparse(redirected_url)
            if (
                parsed_url.scheme == "https"
                and parsed_url.netloc == "query.wikidata.org"
            ):
                sparql_query = urllib.parse.unquote(parsed_url.fragment)

        except Exception as ex:
            print(f"Error fetching URL: {ex}")

        return sparql_query
