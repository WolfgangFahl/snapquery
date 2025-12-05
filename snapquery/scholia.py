"""
Created on 2024-05-04

@author: wf
"""

import requests
from tqdm import tqdm

from snapquery.github_access import GitHub
from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet


class ScholiaQueries:
    """
    A class to handle the extraction and management of Scholia queries.
    """

    def __init__(self, nqm: NamedQueryManager, debug: bool = False):
        """
        Constructor

        Args:
            nqm (NamedQueryManager): The NamedQueryManager to use for storing queries.
            debug (bool): Enable debug output. Defaults to False.
        """
        self.nqm = nqm
        self.named_query_set = NamedQuerySet(
            domain="scholia.toolforge.org",
            namespace="named_queries",
            target_graph_name="wikidata",
        )
        self.github = GitHub(owner="WDscholia", repo="scholia")
        self.debug = debug

    def get_scholia_file_list(self):
        """
        Retrieve the list of SPARQL files from the Scholia repository.

        Returns:
            list: List of dictionaries representing file information.
        """
        file_list_lod = self.github.get_contents("scholia/app/templates")
        return file_list_lod

    def extract_query(self, file_info) -> NamedQuery:
        """
        Extract a single query from file information.

        Args:
            file_info (dict): Dictionary containing information about the file.

        Returns:
            NamedQuery: The extracted NamedQuery object.
        """
        file_name = file_info["name"]
        if file_name.endswith(".sparql") and file_name[:-7]:
            file_response = requests.get(file_info["download_url"])
            file_response.raise_for_status()
            query_str = file_response.text
            name = file_name[:-7]
            named_query = NamedQuery(
                domain=self.named_query_set.domain,
                namespace=self.named_query_set.namespace,
                name=name,
                url=file_info["download_url"],
                title=name,
                description=name,
                comment="",
                sparql=query_str,
            )
            return named_query

    def extract_queries(self, limit: int = None, show_progress: bool = False):
        """
        Extract all queries from the Scholia repository.

        Args:
            limit (int, optional): Limit the number of queries fetched. Defaults to None.
            show_progress (bool, optional): Show a progress bar. Defaults to False.
        """
        file_list_json = self.get_scholia_file_list()
        # Determine iterator loop
        if show_progress:
            iterator = tqdm(file_list_json, desc="Extracting Scholia queries", unit="file")
        else:
            iterator = file_list_json

        for i, file_info in enumerate(iterator, start=1):
            named_query = self.extract_query(file_info)
            if named_query:
                self.named_query_set.queries.append(named_query)
                if self.debug and not show_progress:
                    if i % 80 == 0:
                        print(f"{i}")
                    print(".", end="", flush=True)
                if limit and len(self.named_query_set.queries) >= limit:
                    break

        if self.debug:
            print(f"found {len(self.named_query_set.queries)} scholia queries")

    def save_to_json(self, file_path: str = "/tmp/scholia-queries.json"):
        """
        Save the NamedQueryList to a JSON file.

        Args:
            file_path (str): Path to the JSON file.
        """
        self.named_query_set.save_to_json_file(file_path, indent=2)

    def store_queries(self):
        """
        Store the named queries into the database.
        """
        self.nqm.store_named_query_list(self.named_query_set)
