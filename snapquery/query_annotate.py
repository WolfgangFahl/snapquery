"""
Created on 2024-05-15

@author: tholzheim
"""

from bs4 import BeautifulSoup
from lodstorage.query import Query, QuerySyntaxHighlight


class SparqlQueryAnnotater:
    def __init__(self, query: Query):
        self.query = query
        query_syntax_highlight = QuerySyntaxHighlight(query)
        html = query_syntax_highlight.highlight()
        self.soup = BeautifulSoup(html, "html.parser")

    def get_used_properties(self):
        prefix_element = self.soup.find_all("span", {"class": "nn"})
        properties = []
        for element in prefix_element:
            prefix = element.text
            item = element.next_sibling.next_sibling.text
            properties.append(f"{prefix}:{item}")
        return properties

    def annotate(self) -> str:
        prefix_element = self.soup.find_all("span", {"class": "nn"})
        for element in prefix_element:
            prefix = element
            colon = element.next_sibling
            item = element.next_sibling.next_sibling
            annotation_element = self.soup.new_tag(
                "a", href="http://www.wikidata.org/entity/" + item.text, title=item.text
            )
            prefix.insert_before(annotation_element)
            annotation_element.insert(0, prefix)
            annotation_element.insert(1, colon)
            annotation_element.insert(2, item)
        return str(self.soup)
