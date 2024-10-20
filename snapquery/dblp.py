"""
Created on 2024-06-07

@author: wf
"""

from typing import List

from snapquery.models.person import Person
from snapquery.snapquery_core import NamedQuery, NamedQueryManager


class DblpPersonLookup:
    """
    lookup persons in dblp
    """

    def __init__(self, nqm: NamedQueryManager, endpoint_name: str = "dblp"):
        self.nqm = nqm
        self.endpoint_name = endpoint_name

    def search(self, name_part: str, limit: int = 10) -> List[Person]:
        """
        search persons by part of their name using a SPARQL query with regex.

        Args:
            name_part (str): The part of the name to search for.
            limit (int): The maximum number of results to return.

        Returns:
            List[Person]: A list of Person objects.
        """
        named_query = NamedQuery(
            domain="dblp.org",
            namespace="pid-lookup",
            name="person-by-name-part",
            title="Lookup persons with a name matching a pattern",
            description="Search for persons by matching part of their name using regex",
            sparql="""# snapquery person lookup by name part
SELECT DISTINCT 
  ?author 
  ?label 
  ?dblp_author_id 
  ?wikidata_id 
  ?orcid_id
WHERE {
  ?author a dblp:Person.
  ?author rdfs:label ?label.
  FILTER regex(?label, "{{ name_regex }}", "i")
  OPTIONAL {
    ?author datacite:hasIdentifier ?identifier.
    ?identifier datacite:usesIdentifierScheme datacite:dblp.
    ?identifier litre:hasLiteralValue ?dblp_author_id.
  }
  OPTIONAL {
    ?author datacite:hasIdentifier ?identifier2.
    ?identifier2 datacite:usesIdentifierScheme datacite:wikidata.
    ?identifier2 litre:hasLiteralValue ?wikidata_id.
  }
  OPTIONAL {
    ?author datacite:hasIdentifier ?identifier3.
    ?identifier3 datacite:usesIdentifierScheme datacite:orcid.
    ?identifier3 litre:hasLiteralValue ?orcid_id.
  }
}
            """,
        )
        params_dict = {"name_regex": name_part}

        person_lod, _stats = self.nqm.execute_query(
            named_query=named_query,
            params_dict=params_dict,
            endpoint_name=self.endpoint_name,
            limit=limit,
            with_stats=False,
        )
        persons = []
        for pr in person_lod:
            person = Person(
                label=pr.get("label"),
                wikidata_id=pr.get("wikidata_id"),
                dblp_author_id=pr.get("dblp_author_id"),
                orcid_id=pr.get("orcid_id"),
            )
            person.parse_label()
            persons.append(person)
        return persons
