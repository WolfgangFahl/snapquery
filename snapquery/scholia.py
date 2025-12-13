"""
Created on 2024-05-04
2025-12-11 refactored using Gemini Pro 3 to abstract and make available via command line


@author: wf
"""
import requests
from tqdm import tqdm
from typing import Optional

from snapquery.github_access import GitHub
from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet

class GitHubQueries:
    """
    A general class to handle the extraction and management of queries
    hosted in a GitHub repository.
    """

    def __init__(
        self,
        nqm: NamedQueryManager,
        owner: str,
        repo: str,
        path: str = "",
        extension: str = ".sparql",
        domain: Optional[str] = None,
        namespace: Optional[str] = None,
        target_graph: str = "wikidata",
        debug: bool = False
    ):
        """
        Constructor
        """
        self.nqm = nqm
        self.owner = owner
        self.repo = repo
        self.path = path
        self.extension = extension
        self.debug = debug

        self.domain = domain if domain else f"{repo}.github.com"
        self.namespace = namespace if namespace else "imported_queries"

        self.named_query_set = NamedQuerySet(
            domain=self.domain,
            namespace=self.namespace,
            target_graph_name=target_graph,
        )
        self.github = GitHub(owner=owner, repo=repo)

    def extract_query(self, file_info: dict) -> Optional[NamedQuery]:
        """
        Extract a single query from file information.
        """
        named_query = None
        file_name = file_info.get("name")

        if file_name and file_name.endswith(self.extension):
            file_url = file_info.get("download_url")
            if file_url:
                try:
                    response = requests.get(file_url)
                    response.raise_for_status()
                    query_str = response.text

                    name = file_name[: -len(self.extension)]

                    named_query = NamedQuery(
                        domain=self.named_query_set.domain,
                        namespace=self.named_query_set.namespace,
                        name=name,
                        url=file_url,
                        title=name,
                        description=f"Imported from {self.owner}/{self.repo}",
                        comment=f"Path: {file_info.get('path')}",
                        sparql=query_str,
                    )
                except Exception as e:
                    if self.debug:
                        print(f"Failed to extract query from {file_name}: {e}")

        return named_query

    def extract_queries(self, limit: int = None, show_progress: bool = False):
        """
        Extract queries from the GitHub repository recursively matching the configuration.
        """
        if self.debug:
            print(f"Fetching file list from {self.owner}/{self.repo} path: '{self.path}'...")

        file_list = self.github.list_files_recursive(self.path, suffix=self.extension)

        if show_progress:
            iterator = tqdm(file_list, desc=f"Extracting {self.extension} files", unit="file")
        else:
            iterator = file_list

        count = 0
        for i, file_info in enumerate(iterator, start=1):
            named_query = self.extract_query(file_info)
            if named_query:
                self.named_query_set.queries.append(named_query)
                count += 1

                if self.debug and not show_progress:
                    if i % 80 == 0:
                        print(f"{i}")
                    print(".", end="", flush=True)

                if limit and count >= limit:
                    break

        if self.debug:
            print(f"\nFound {len(self.named_query_set.queries)} queries in {self.owner}/{self.repo}")

    def store_queries(self):
        """
        Store the named queries into the database.
        """
        self.nqm.store_named_query_list(self.named_query_set)

    def save_to_json(self, file_path: str = "/tmp/scholia-queries.json"):
        """
        Save the NamedQueryList to a JSON file.

        Args:
            file_path (str): Path to the JSON file.
        """
        self.named_query_set.save_to_json_file(file_path, indent=2)



class ScholiaQueries(GitHubQueries):
    """
    Specific implementation for Scholia Queries.
    """
    def __init__(self, nqm: NamedQueryManager, debug: bool = False):
        super().__init__(
            nqm=nqm,
            owner="WDscholia",
            repo="scholia",
            path="scholia/app/templates",
            extension=".sparql",
            domain="scholia.toolforge.org",
            namespace="named_queries",
            debug=debug
        )