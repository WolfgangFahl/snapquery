"""
Created on 2024-05-26
@author: wf
"""

from ez_wikidata.wdsearch import WikidataSearch

from snapquery.orcid import OrcidAuth, OrcidSearchParams
from snapquery.dblp import DblpPersonLookup
from snapquery.pid import PIDs
from snapquery.models.person import Person
from typing import List
from snapquery.snapquery_core import NamedQueryManager, NamedQuery


class PersonLookup:
    """
    Lookup potential persons from various 
    databases such as Wikidata, ORCID, and DBLP.
    """

    def __init__(self, nqm: NamedQueryManager):
        """
        Initialize the PersonLookup with a Named Query Manager.

        Args:
            nqm (NamedQueryManager): The named query manager to execute SPARQL queries.
        """
        self.pids = PIDs()
        self.nqm = nqm
        self.wikidata_search = WikidataSearch()
        self.dblp_person_lookup=DblpPersonLookup(self.nqm)

    def suggest_from_wikidata(self, search_name: str, limit: int = 10) -> List[Person]:
        """
        Suggest persons using WikidataSearch.

        Args:
            search_name (str): The name to search for suggestions.
            limit (int): The maximum number of results to return.

        Returns:
            List[Person]: A list of suggested persons from Wikidata.
        """
        persons = []
        suggestions = self.wikidata_search.searchOptions(search_name, limit=limit)
        qid_list = ""
        delim = ""
        for qid, _plabel, _pdesc in suggestions:
            qid_list += f"{delim}wd:{qid}"
            delim = " "
        named_query = NamedQuery(
            namespace="pid-lookup",
            name="person-by-qid",
            title="Lookup persons with the given qids",
            description="based on a pre-search with wikidata search select persons",
            sparql="""# snapquery person lookup 
SELECT *
WHERE 
{
  VALUES ?scholar {
    {{ qid_list }}
  } 
  ?scholar wdt:P31 wd:Q5 .
  ?scholar wdt:P735 ?given_name_qid .
  ?given_name_qid rdfs:label ?given_name .
  ?scholar wdt:P734 ?family_name_qid .
  ?family_name_qid rdfs:label ?family_name .
  OPTIONAL{{ ?scholar rdfs:label ?label FILTER(lang(?label) = "en") }}.
  OPTIONAL{{?scholar wdt:P2456 ?dblp_author_id .}}
  OPTIONAL{{?scholar wdt:P496 ?orcid_id . }}
  OPTIONAL{{?scholar wdt:P18 ?image . }}
  FILTER(lang(?given_name) = "en")
  FILTER(lang(?family_name) = "en")
}
            """,
        )
        params_dict = {"qid_list": qid_list}
        person_lod, stats = self.nqm.execute_query(
            named_query=named_query,
            params_dict=params_dict,
            limit=limit,
            with_stats=False,
        )
        for pr in person_lod:
            person = Person(
                label=pr.get("label"),
                given_name=pr.get("given_name"),
                family_name=pr.get("family_name"),
                wikidata_id=pr.get("scholar").split("/")[-1],
                dblp_author_id=pr.get("dblp_author_id"),
                orcid_id=pr.get("orcid_id"),
                image=pr.get("image"),
            )
            persons.append(person)

        return persons

    def suggest_from_orcid(self, search_name: str, limit: int = 10) -> List[Person]:
        """
        Suggest persons using the ORCID registry search.

        Args:
            search_name (str): The name to search for suggestions.
            limit (int): The maximum number of results to return.

        Returns:
            List[Person]: A list of suggested persons from ORCID.
        """
        orcid = OrcidAuth()
        persons = []
        if orcid.available():
            persons = orcid.search(
                OrcidSearchParams(family_name=search_name), limit=limit
            )
        return persons
    
    def suggest_from_dblp(self, search_name: str, limit: int = 10) -> List[Person]:
        """
        Suggest persons using DBLP author search.

        Args:
            search_name (str): The name to search for suggestions.
            limit (int): The maximum number of results to return.

        Returns:
            List[Person]: A list of suggested persons from DBLP.
        """
        persons=self.dblp_person_lookup.search(name_part=search_name, limit=limit)
        return persons
    