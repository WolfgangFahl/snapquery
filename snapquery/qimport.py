"""
Created on 2024-05-05

@author: wf
"""

from tqdm import tqdm

from snapquery.snapquery_core import NamedQueryList, NamedQueryManager
from snapquery.wd_short_url import ShortUrl

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
                short_url = ShortUrl(nq.url)
                nq.sparql = short_url.read_query()  
            if with_store and self.nqm:
                self.nqm.add_and_store(nq)
        return nq_list