"""
Created on 2024-05-26
@ author: wf
"""
from ez_wikidata.wdsearch import WikidataSearch
from snapquery.pid import PIDs, PIDValue, PID
from snapquery.models.person import Person
from typing import List
from snapquery.snapquery_core import NamedQueryManager, NamedQuery

class PersonLookup:
    """
    Lookup potential persons
    """
    
    def __init__(self,nqm:NamedQueryManager):
        """
        constructor
        """
        self.pids = PIDs()
        self.nqm=nqm
        self.wikidata_search = WikidataSearch()

    def suggest(self, search_name: str, limit:int=10) -> List[Person]:
        """
        Suggest names using WikidataSearch

        Args:
            search_name (str): The name to search for suggestions.
        """
        persons=[]
        suggestions = self.wikidata_search.searchOptions(search_name,limit=limit)
        qid_list=""
        delim=""
        for qid,_plabel,_pdesc in suggestions:
            qid_list+=f"{delim}wd:{qid}"
            delim=" "
        named_query=NamedQuery(
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
            """
        )
        params_dict={"qid_list":qid_list}
        person_lod,stats=self.nqm.execute_query(
            named_query=named_query,
            params_dict=params_dict,
            limit=limit,
            with_stats=False)
        for pr in person_lod:
            person = Person(
                label=pr.get("label"),
                given_name=pr.get("given_name"),
                family_name=pr.get("family_name"),
                wikidata_id=pr.get("scholar").split('/')[-1],
                dblp_author_id=pr.get("dblp_author_id"),
                orcid_id=pr.get("orcid_id"),
                image=pr.get("image")
            )
            persons.append(person)
            
        return persons
        