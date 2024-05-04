"""
Created on 2024-05-04

@author: tholzheim
"""

import pprint
import unittest
import re
import requests
import wikitextparser as wtp
from wikitextparser import Section, Template

from snapquery.snapquery_core import NamedQuery


class TestWdQueryParsing(unittest.TestCase):
    def _get_examples_wikitext(self) -> str:
        """Get wiki text with SPARQL query examples"""
        url = "https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples?action=raw"
        res = requests.get(url)
        return res.text

    def _extract_query_from_section(self, section: Section) -> NamedQuery:
        """
        Extract named query from section
        """
        query = self._get_sparql_template(section.templates)
        named_query = None
        if query:
            desc = section.plain_text()
            title = self._sanitize_title(section.title).strip()
            named_query = NamedQuery(
                namespace="wikidata-examples",
                name=title,
                title=title,
                description=desc,
                sparql=query.arguments[0].value,
            )
        return named_query

    def _sanitize_title(self, section_title: str) -> str:
        """
        Sanitize section title by removing translate tags
        """
        pattern = r"""<translate><!--T:\d+-->(?P<name>[\w\d\s.\-,\\=<>/|{}()"'&]+)<\/translate>"""
        match = re.search(pattern, section_title)
        if match:
            title = match.group("name")
        else:
            title = section_title
        return title

    def _get_sparql_template(self, templates: list[Template]) -> Template:
        """
        Get sparql template of the list of templates
        If the list contains more than one sparql template None is returned.
        """
        queries = []
        for template in templates:
            if template.name == "SPARQL":
                queries.append(template)
        # ToDo: Handle sections with multiple queries
        return queries[0] if len(queries) == 1 else None

    def test_wikidata_examples_query_extraction(self):
        """
        test extraction and parsing of wikidata example queries to NamedQueries

        Queries can be found at https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples
        """
        wikitext = self._get_examples_wikitext()
        parsed = wtp.parse(wikitext)
        queries = []
        for section in parsed.sections:
            nq = self._extract_query_from_section(section)
            if nq:
                queries.append(nq)
                pprint.pprint(nq)


if __name__ == "__main__":
    unittest.main()
