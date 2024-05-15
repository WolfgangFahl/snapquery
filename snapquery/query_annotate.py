"""
Created on 2024-05-15

@author: tholzheim
"""

import dataclasses
import re
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from lodstorage.query import Query, QuerySyntaxHighlight
from lodstorage.yamlable import lod_storable


class SparqlQueryAnnotater:
    """
    Annotate a query
    """

    def __init__(self, query: Query):
        self.query = query
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
        return str(self.soup)


@lod_storable
class Stats:
    name: str
    item_stats: list["ItemStat"] = dataclasses.field(default_factory=list)

    def get_by_id(self, identifier: str) -> Optional["ItemStat"]:
        for stat in self.item_stats:
            if stat.identifier == identifier:
                return stat

    def get_property_stats(self):
        return [stat for stat in self.item_stats if not stat.is_item()]

    def get_entity_stats(self):
        return [stat for stat in self.item_stats if stat.is_item()]


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
            if namespace_stat.name == namespace:
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

    name: str
    count: int = 0


QUERY_ITEM_STATS: Stats = Stats.load_from_yaml_file(
    Path(__file__).parent.joinpath("samples", "query_stats.yaml")
)
