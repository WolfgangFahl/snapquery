"""
Created on 2024-05-05

@author: wf
"""
import glob
import json
import os
from tqdm import tqdm

from snapquery.snapquery_core import NamedQueryManager, NamedQuerySet
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
    
    def import_samples(self,with_store:bool = True, show_progress:bool=False):
        """
        import all sample json files
        
        Args:
            with_store(bool): if True store the result
            show_progress(bool): if True show a tqdm progress bar
        """
        for json_file in glob.glob(os.path.join(self.nqm.samples_path, "*.json")):            
            try:
                nq_list = self.import_from_json_file(
                    json_file, with_store, show_progress
                )
            except Exception as ex:
                print(f"could not load json_file {json_file}")
                raise ex
            if "ceur" in json_file:
                json_file_name = os.path.basename(json_file)
                output_path = os.path.join("/tmp", json_file_name)
                nq_list.save_to_json_file(output_path, indent=2)
                pass

    def import_from_json_file(
        self, json_file: str, with_store: bool = False, show_progress: bool = False
    ) -> NamedQuerySet:
        """
        Import named queries from a JSON file.

        Args:
            json_file (str): Path to the JSON file.
            with_store (bool): If True, store the results in the NamedQueryManager.
            show_progress (bool): If True, show a progress bar during the import.

        Returns:
            NamedQuerySet: A NamedQuerySet object containing the imported NamedQuery objects.
        """
        nq_set = NamedQuerySet.load_from_json_file(json_file)
        iterable = (
            tqdm(nq_set.queries, desc=f"Importing Namespace {nq_set.namespace}@{nq_set.domain}")
            if show_progress
            else nq_set.queries
        )

        for nq in iterable:
            if not nq.sparql:
                if nq.url and nq.url.startswith("https://w.wiki/"):
                    short_url = ShortUrl(nq.url)
                    nq.sparql = short_url.read_query()
                else:
                    raise Exception(f"invalid named query with no url: {nq}")
                    # what now?
                    continue    
            if with_store and self.nqm:
                self.nqm.add_and_store(nq)
        return nq_set
