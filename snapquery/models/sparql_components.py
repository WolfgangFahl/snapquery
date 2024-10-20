import json
from pathlib import Path
from typing import Union

from lodstorage.query import EndpointManager
from lodstorage.sparql import SPARQL
from pydantic import AnyHttpUrl, BaseModel
from snapquery.snapquery_core import NamedQuerySet


class SparqlComponent(BaseModel):
    """
    component of the sparql language
    """

    name: str
    wikidata_entity: AnyHttpUrl


class SPARQLFunction(SparqlComponent):
    """
    sparql function
    """


class SPARQLKeyword(SparqlComponent):
    """
    sparql keyword
    """


class SPARQLLanguage(BaseModel):
    keywords: list[SPARQLKeyword]
    functions: list[SPARQLFunction]

    def get_keyword_wd_entity(self, name: str) -> AnyHttpUrl:
        """
        Get the wikidata entity for a given SPARQL keyword
        Args:
            name: name of the SPARQL keyword

        Returns:
            wikidata entity IRI
        """
        return self._get_component_wd_entity(name=name, data=self.keywords)

    def get_function_wd_entity(self, name: str) -> AnyHttpUrl:
        """
        Get the wikidata entity for a given SPARQL function
        Args:
            name: name of the SPARQL keyword

        Returns:
            wikidata entity IRI
        """
        return self._get_component_wd_entity(name=name, data=self.functions)

    def _get_component_wd_entity(
        self, name: str, data: list[SparqlComponent]
    ) -> Union[AnyHttpUrl, None]:
        name = name.upper()
        for component in data:
            if name == component.name:
                return component.wikidata_entity
        return None

    @classmethod
    def _get_cache_path(cls) -> Path:
        return Path(__file__).parent.parent.joinpath(
            "resources", "sparql_language.json"
        )

    @classmethod
    def load_sparql_language_data_from_wikidata(
        cls, cache: bool = True
    ) -> "SPARQLLanguage":
        """
        Query the SPARQL language data from wikidata
        """
        samples_dir = Path(__file__).parent.parent.joinpath("samples")
        query_filepath = samples_dir.joinpath("snapquery.json")
        endpoints_path = samples_dir.joinpath("endpoints.yaml")
        nq_set: NamedQuerySet = NamedQuerySet.load_from_json_file(query_filepath)
        query_functions = nq_set.get_query_by_id(
            "sparql-functions--snapquery@wikidata.org"
        )
        query_keywords = nq_set.get_query_by_id(
            "sparql-keywords--snapquery@wikidata.org"
        )
        endpoints = EndpointManager.getEndpoints(
            endpointPath=str(endpoints_path), lang="sparql", with_default=False
        )
        endpoint = endpoints.get(nq_set.target_graph_name)
        sparql = SPARQL(endpoint.endpoint, method=endpoint.method)
        sparql_language_record = {}
        sparql_language_record["functions"] = sparql.queryAsListOfDicts(
            query_functions.sparql
        )
        sparql_language_record["keywords"] = sparql.queryAsListOfDicts(
            query_keywords.sparql
        )
        sparql_language = SPARQLLanguage.model_validate(sparql_language_record)
        if cache:
            json_string = sparql_language.model_dump(mode="json")
            path = cls._get_cache_path()
            path.write_text(json.dumps(json_string, indent=4))
        return sparql_language

    @classmethod
    def load_sparql_language(cls) -> "SPARQLLanguage":
        """
        loaf SPARQLLanguage data from cache
        Returns:
            SPARQLLanguage
        """
        path = cls._get_cache_path()
        json_str = json.loads(path.read_text())
        sparql_language = SPARQLLanguage.model_validate(json_str)
        return sparql_language
