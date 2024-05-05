"""
Created on 2024-05-05

@author: wf
"""
from tqdm import tqdm
import urllib.parse
import json
import requests
from snapquery.snapquery_core import NamedQuery, NamedQueryManager
from typing import List

class QueryImport:
    """
    import named queries from a given url
    """

    def __init__(self,nqm:NamedQueryManager=None):
        self.nqm=nqm
        pass
    
    def import_from_json_file(self, 
        json_file: str, 
        with_store:bool=False,
        show_progress:bool=False) -> List[NamedQuery]:
        """
        Import named queries from a JSON file.

        Args:
            json_file (str): Path to the JSON file.
            with_store(bool): if True store the result

        Returns:
            List[NamedQuery]: A list of NamedQuery objects imported from the JSON file.
        """
        with open(json_file, 'r') as f:
            data = json.load(f)

        queries = []
        lod=[]
        iterable = tqdm(data, desc="Importing Named Queries") if show_progress else data
        known_queries = []
        for record in iterable:
            if record.get('url'):
                nq=NamedQuery.from_record(record)
                if not nq.sparql and nq.url.startswith("https://w.wiki/"):
                    nq.sparql=self.read_from_short_url(nq.url)
                if nq.name not in known_queries:
                    known_queries.append(nq.name)
                else:
                    continue
                lod.append(nq.as_record())
                queries.append(nq)
        if with_store and self.nqm:
            self.nqm.store(lod)
        return queries

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
            if not self.solution:
                print(f"Error fetching URL: {ex}")
            else:
                self.solution.handle_exception(ex)
        return sparql_query
