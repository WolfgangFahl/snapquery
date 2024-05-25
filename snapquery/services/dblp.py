"""
Created 2023

@author: th
"""
from typing import List, Optional

import requests
from lodstorage.sparql import SPARQL

from snapquery.models.person import Person


class Dblp:
    """
    dblp computer science bibliography access
    https://dblp.org/
    """

    def __init__(self, sparql_endpoint_url: Optional[str] = None, endpoint_url: Optional[str] = None):
        if sparql_endpoint_url is None:
            sparql_endpoint_url = "https://sparql.dblp.org/sparql"
        if endpoint_url is None:
            endpoint_url = "https://dblp.uni-trier.de/search/author/api"
        self.sparql_endpoint = SPARQL(sparql_endpoint_url)
        self.endpoint_url = endpoint_url

    def get_person_suggestions(self, search_mask: Person) -> List[Person]:
        """
        Given a search mask query wikidata  for matching persons
        Args:
            search_mask:

        Returns:

        """
        payload = {}
        headers = {}
        params = {
            "format": "json",
            "q": f"{search_mask.given_name} {search_mask.family_name}"
        }

        response = requests.request("GET", self.endpoint_url, headers=headers, data=payload, params=params)
        qres = response.json()
        qres_hits = qres.get("result").get("hits").get("hit")
        res = []
        if qres_hits is not None:
            hits = [hit.get("info").get("url") for hit in qres_hits]
            person_urls = "\n".join([f"<{url}>" for url in hits])
            query = f"""
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dblp: <https://dblp.org/rdf/schema#>
                PREFIX datacite: <http://purl.org/spar/datacite/>
                PREFIX litre: <http://purl.org/spar/literal/> 
                SELECT DISTINCT ?author ?label ?dblp_author_id ?wikidata_id ?orcid_id WHERE {{
                VALUES ?author {{
                        {person_urls}
                }}
                    ?author a dblp:Person.
                    ?author rdfs:label ?label
                  OPTIONAL{{
                    OPTIONAL{{
                    ?author datacite:hasIdentifier ?identifier .
                    ?identifier datacite:usesIdentifierScheme datacite:dblp.
                    ?identifier litre:hasLiteralValue ?dblp_author_id .
                    }}
                    OPTIONAL{{
                    ?author datacite:hasIdentifier ?identifier2 .
                    ?identifier2 datacite:usesIdentifierScheme datacite:wikidata.
                    ?identifier2 litre:hasLiteralValue ?wikidata_id .
                    }}
                    OPTIONAL{{
                    ?author datacite:hasIdentifier ?identifier3 .
                    ?identifier3 datacite:usesIdentifierScheme datacite:orcid.
                    ?identifier3 litre:hasLiteralValue ?orcid_id .
                    }}
                  }}
                }}
            """
            lod = self.sparql_endpoint.queryAsListOfDicts(query)
            for d in lod:
                person = Person(
                        label=d.get("label"),
                        wikidata_id=d.get("wikidata_id"),
                        dblp_author_id=d.get("dblp_author_id"),
                        orcid_id=d.get("orcid_id")
                )
                res.append(person)
        return res