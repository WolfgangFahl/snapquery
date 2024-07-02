"""
Created on 2024-07-02
@author: wf
"""

from wikibot3rd.smw import SMWClient
from wikibot3rd.wikiclient import WikiClient

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet


class CeurWSQueries:
    """
    A class to handle the extraction and management of CEUR-WS queries.
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
            domain="ceur-ws.org",
            namespace="challenge",
            target_graph_name="wikidata",
        )
        self.debug = debug
        self.wiki_id = "cr"
        self.wiki_client = WikiClient.ofWikiId(self.wiki_id)
        self.smw = SMWClient(self.wiki_client.getSite())

    def extract_queries(self, limit: int = None):
        """
        Extract all queries from the CEUR-WS challenge wiki.
        Args:
            limit (int, optional): Limit the number of queries fetched. Defaults to None.
        """
        if limit:
            limitclause=f"|limit={limit}"
        else:
            limitclause=""
        ask_query = f"""{{{{#ask: [[Concept:Query]]
|mainlabel=Query
|?Query id=id
|?Query name=name
|?Query title=title
|?Query tryiturl=tryiturl
|?Query wdqsurl=wdqsurl
|?Query scholia=scholia
|?Query relevance=relevance
|?Query task=task
|?Query sparql=sparql
{limitclause}
|sort=Query task,Query id
|order=ascending
}}}}"""
        query_results = self.smw.query(ask_query)
        for _page_title, query_data in query_results.items():
            # Extract values into local variables for easier debugging
            name = query_data.get("name")
            url = query_data.get("wdqsurl")
            if not url:
                continue
            title = query_data.get("title")
            description = query_data.get("task")
            sparql = query_data.get("sparql")
            if url:
                url=f"https://w.wiki/{url}"
            tryiturl = query_data.get("tryiturl")
            if tryiturl:
                tryiturl=f"https://qlever.cs.uni-freiburg.de/wikidata/{tryiturl}"
            comment = f"qlever tryit url: {tryiturl}" if tryiturl else None
            named_query = NamedQuery(
                domain=self.named_query_set.domain,
                namespace=self.named_query_set.namespace,
                name=name,
                url=url,
                title=title,
                description=description,
                sparql=sparql,
                comment=comment,
            )
            self.named_query_set.queries.append(named_query)

            if self.debug:
                print(".", end="", flush=True)
                if len(self.named_query_set.queries) % 80 == 0:
                    print(f"{len(self.named_query_set.queries)}")

        if self.debug:
            print(
                f"\nFound {len(self.named_query_set.queries)} CEUR-WS challenge queries"
            )

    def save_to_json(self, file_path: str = "/tmp/ceurws-queries.json"):
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
