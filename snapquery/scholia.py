"""
Created on 2024-05-04

@author: wf
"""

import requests

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet


class ScholiaQueries:
    """
    A class to handle the extraction and management of Scholia queries.
    """

    repository_url = "https://api.github.com/repos/WDscholia/scholia/contents/scholia/app/templates"

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
        self.debug = debug

    def get_scholia_file_list(self):
        """
        Retrieve the list of SPARQL files from the Scholia repository.

        Returns:
            list: List of dictionaries representing file information.
        """
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(self.repository_url, headers=headers)
        response.raise_for_status()  # Ensure we notice bad responses
        return response.json()

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
            return NamedQuery(
                domain=self.named_query_set.domain,
                namespace=self.named_query_set.namespace,
                name=name,
                url=file_info["download_url"],
                title=name,
                description=name,
                comment="",
                sparql=query_str,
            )

    def extract_queries(self, limit: int = None):
        """
        Extract all queries from the Scholia repository.

        Args:
            limit (int, optional): Limit the number of queries fetched. Defaults to None.
        """
        file_list_json = self.get_scholia_file_list()
        for i, file_info in enumerate(file_list_json, start=1):
            named_query = self.extract_query(file_info)
            if named_query:
                self.named_query_set.queries.append(named_query)
                if self.debug:
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
