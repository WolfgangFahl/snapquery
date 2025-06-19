"""
Created on 2024-05-15

@author: tholzheim
"""

import dataclasses
import re
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, ResultSet
from lodstorage.query import Query, QuerySyntaxHighlight
from basemkit.yamlable import lod_storable

from snapquery.models.sparql_components import SPARQLLanguage


class SparqlQueryAnnotater:
    """
    Annotate a query
    """

    def __init__(self, query: Query):
        self.query = query
        self.sparql_language = SPARQLLanguage.load_sparql_language()
        query_syntax_highlight = QuerySyntaxHighlight(query)
        html = query_syntax_highlight.highlight()
        self.soup = BeautifulSoup(html, "html.parser")
        self.stats = QUERY_ITEM_STATS

    def get_used_properties(self):
        prefix_element = self.soup.find_all("span", {"class": "nn"})
        properties = []
        for element in prefix_element:
            item = element.next_sibling.next_sibling
            if hasattr(item, "attrs") and "nt" in item.attrs.get("class"):
                properties.append(f"{element.text}:{item.text}")
        return properties

    def annotate(self) -> str:
        self._annotate_items()
        self._annotate_keywords()
        self._annotate_namespace_iris()
        self._annotate_functions()
        return str(self.soup)

    def _annotate_items(self):
        prefix_element = self.soup.find_all("span", {"class": "nn"})
        for element in prefix_element:
            prefix = element
            colon = element.next_sibling
            item = element.next_sibling.next_sibling
            if hasattr(item, "attrs") and "nt" in item.attrs.get("class"):
                identifier = item.text
                if not identifier.startswith(("P", "Q")):
                    identifier = f"{prefix.text}:{identifier}"
                item_stat = self.stats.get_by_id(identifier)
                title = item_stat.label if item_stat else item.text
                annotation_element = self.soup.new_tag(
                    "a",
                    href="http://www.wikidata.org/entity/" + item.text,
                    title=title,
                    target="_blank",
                )
                prefix.insert_before(annotation_element)
                annotation_element.insert(0, prefix)
                annotation_element.insert(1, colon)
                annotation_element.insert(2, item)

    def _annotate_namespace_iris(self):
        """
        Convert the namespace IRIs
        """
        for element in self._get_namespace_iri_elements():
            namespace_iri = element.next_element.text
            if namespace_iri:
                namespace_iri = namespace_iri.strip("<>")
                annotation_element = self.soup.new_tag(
                    "a",
                    href=namespace_iri,
                    title=namespace_iri,
                    target="_blank",
                )
                element.insert_before(annotation_element)
                annotation_element.insert(0, element)

    def get_namespace_iris(self) -> list[str]:
        namespace_iris = []
        for element in self._get_namespace_iri_elements():
            namespace_iri = element.next_element.text
            if namespace_iri:
                namespace_iri = namespace_iri.strip("<>")
                namespace_iris.append(namespace_iri)
        return namespace_iris

    def _get_namespace_iri_elements(self) -> ResultSet:
        return self.soup.find_all("span", {"class": "nl"})

    def _get_prefix_elements(self) -> ResultSet:
        return self.soup.find_all("span", {"class": "nn"})

    def _get_keyword_elements(self):
        return self.soup.find_all("span", {"class": "k"})

    def _get_function_elements(self):
        elements = []
        for element in self.soup.find_all("span", {"class": "nf"}):
            if element.previous_element.text != "@":
                elements.append(element)
        return elements

    def get_used_prefixes(self):
        prefixes = []
        for element in self._get_prefix_elements():
            prefix = element.next_element.text
            if prefix:
                prefixes.append(prefix)
        return prefixes

    def get_used_functions(self):
        keywords = []
        for element in self._get_function_elements():
            keyword = element.next_element.text
            if keyword:
                keywords.append(keyword)
        return keywords

    def get_used_keywords(self):
        keywords = []
        for element in self._get_keyword_elements():
            keyword = element.next_element.text
            if keyword:
                keywords.append(keyword)
        return keywords

    def get_normalized_keywords(self):
        values = self.get_used_keywords()
        return self._normalize(values)

    def get_normalized_functions(self):
        values = self.get_used_functions()
        return self._normalize(values)

    def _normalize(self, values: list[str]) -> list[str]:
        normalized_values = [value.upper() for value in values]
        return normalized_values

    def _annotate_keywords(self):
        for element in self._get_keyword_elements():
            keyword = element.next_element.text
            annotation_element = self.soup.new_tag(
                "a",
                href=self.sparql_language.get_keyword_wd_entity(keyword),
                title=keyword.upper(),
                target="_blank",
            )
            element.insert_before(annotation_element)
            annotation_element.insert(0, element)

    def _annotate_functions(self):
        for element in self._get_function_elements():
            function_name = element.next_element.text
            annotation_element = self.soup.new_tag(
                "a",
                href=self.sparql_language.get_function_wd_entity(function_name),
                title=function_name.upper(),
                target="_blank",
            )
            element.insert_before(annotation_element)
            annotation_element.insert(0, element)


@lod_storable
class Stats:
    name: str
    item_stats: list["ItemStat"] = dataclasses.field(default_factory=list)
    keyword_stats: list["KeywordStat"] = dataclasses.field(default_factory=list)
    function_stats: list["FunctionStat"] = dataclasses.field(default_factory=list)
    namespace_stats: list["NamespaceStat"] = dataclasses.field(default_factory=list)

    def get_by_id(self, identifier: str) -> Optional["ItemStat"]:
        for stat in self.item_stats:
            if stat.identifier == identifier:
                return stat

    def get_property_stats(self):
        return [stat for stat in self.item_stats if not stat.is_item()]

    def get_entity_stats(self):
        return [stat for stat in self.item_stats if stat.is_item()]

    def get_keywords_stats(self):
        return self.keyword_stats

    def get_function_stats(self):
        return self.function_stats

    def get_namespace_stats(self) -> list["NamespaceStat"]:
        return self.namespace_stats


@lod_storable
class KeywordStat:
    keyword: str
    count: int


@lod_storable
class ItemStat:
    identifier: str
    label: str
    count: int = 0
    namespace_stats: list["NamespaceStat"] = dataclasses.field(default_factory=list)

    def is_item(self):
        p = re.compile(r"Q\d+")
        return p.match(self.identifier)

    def increment_namespace_count(self, namespace: str):
        for namespace_stat in self.namespace_stats:
            if namespace_stat.prefix == namespace:
                namespace_stat.count += 1
                return
        namespace_stat = NamespaceStat(namespace)
        namespace_stat.count += 1
        self.namespace_stats.append(namespace_stat)


@lod_storable
class NamespaceStat:
    """
    contains namespace information
    """

    prefix: str
    iri: Optional[str] = None
    count: int = 0


@lod_storable
class FunctionStat:
    """
    contains function information
    """

    name: str
    count: int = 0


QUERY_ITEM_STATS: Stats = Stats.load_from_yaml_file(
    Path(__file__).parent.joinpath("samples", "query_stats.yaml")
)
