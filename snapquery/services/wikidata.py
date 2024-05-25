"""
Created 2023

@author: th
"""
from typing import List, Optional

from lodstorage.sparql import SPARQL

from snapquery.models.person import Scholar


class Wikidata:
    """
    Wikdata access
    """

    def __init__(self, endpoint_url: Optional[str] = None, limit:int=5000):
        if endpoint_url is None:
            endpoint_url = "https://qlever.cs.uni-freiburg.de/api/wikidata"
        self.endpoint = SPARQL(endpoint_url)
        self.limit=limit

    def get_scholar_suggestions(self, search_mask: Scholar) -> List[Scholar]:
        """
        Given a search mask query wikidata  for matching scholars
        Args:
            search_mask:

        Returns:

        """
        filters = ""
        if search_mask.given_name:
            filters += f"""\nFILTER(REGEX(?given_name, "{search_mask.given_name}"))"""
        if search_mask.family_name:
            filters += f"""\nFILTER(REGEX(?family_name, "{search_mask.family_name}"))"""
        if search_mask.wikidata_id:
            filters += f"""VALUES ?scholar {{wd:{search_mask.wikidata_id} }}"""
        query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX wd: <http://www.wikidata.org/entity/>
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            SELECT *
            WHERE 
            {{
              ?scholar wdt:P31 wd:Q5 .
              ?scholar wdt:P735 ?_given_name .
              ?_given_name rdfs:label ?given_name .
              ?scholar wdt:P734 ?_family_name .
              ?_family_name rdfs:label ?family_name .
              OPTIONAL{{ ?scholar rdfs:label ?label FILTER(lang(?label) = "en") }}.
              OPTIONAL{{?scholar wdt:P2456 ?dblp_author_id .}}
              OPTIONAL{{?scholar wdt:P496 ?orcid_id . }}
              OPTIONAL{{?scholar wdt:P18 ?image . }}
              FILTER(lang(?given_name) = "en")
              FILTER(lang(?family_name) = "en")
              {filters}
              
            }}
            LIMIT {self.limit}
        """
        lod = self.endpoint.queryAsListOfDicts(query)
        res = []
        for d in lod:
            qid = d.get("scholar", None)
            if qid:
                qid = qid.replace("http://www.wikidata.org/entity/", "")
                scholar = Scholar(
                    label=d.get("label", None),
                    given_name=d.get("given_name", None),
                    family_name=d.get("family_name", None),
                    wikidata_id=qid,
                    orcid_id=d.get("orcid_id", None),
                    dblp_author_id=d.get("dblp_author_id", None),
                    image=d.get("image", None),
            )
            res.append(scholar)
        return res