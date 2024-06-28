"""
Created on 2024-05-04

Author: tholzheim
"""

import re

import requests
import wikitextparser as wtp
from wikitextparser import Section, Template

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet


class WikidataExamples:
    """
    A class to handle the extraction and management of Wikidata example queries.
    """

    base_url = (
        "https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples"
    )

    def __init__(self, nqm: NamedQueryManager):
        """
        constructor
        """
        self.nqm = nqm
        self.named_query_list = NamedQuerySet(
            namespace="wikidata.org/examples", target_graph_name="wikidata"
        )

    def get_examples_wikitext(self) -> str:
        """
        Get wiki text with SPARQL query examples.

        Returns:
            str: Raw wikitext of the examples page.
        """
        res = requests.get(f"{self.base_url}?action=raw")
        return res.text

    def extract_query_from_section(self, section: Section) -> NamedQuery:
        """
        Extract named query from section.

        Args:
            section (Section): Wikitext section containing a SPARQL query.

        Returns:
            NamedQuery: Extracted named query object.
        """
        query = self.get_sparql_template(section.templates)
        named_query = None
        if query:
            desc = section.plain_text()
            desc = desc.replace("<translate>", "").replace("</translate>", "")
            title = self.sanitize_title(section.title).strip()
            desc = desc.replace(f"====  {title} ====", "").replace(
                f"===  {title} ===", ""
            )
            desc = desc.replace(f"==  {title} ==", "").strip()
            named_query = NamedQuery(
                namespace="wikidata-examples",
                name=title,
                title=title,
                description=desc,
                url=self.base_url,
                sparql=query.arguments[0].value,
            )
        return named_query

    def sanitize_title(self, section_title: str) -> str:
        """
        Sanitize section title by removing translate tags.

        Args:
            section_title (str): Section title containing tags.

        Returns:
            str: Sanitized section title.
        """
        pattern = r"""<translate><!--T:\d+-->(?P<name>[\w\d\s.\-,\\=<>/|{}()"'&]+)<\/translate>"""
        match = re.search(pattern, section_title)
        if match:
            title = match.group("name")
        else:
            title = section_title
        return title

    def get_sparql_template(self, templates: list[Template]) -> Template:
        """
        Get SPARQL template from the list of templates.

        Args:
            templates (list[Template]): List of Wikitext templates.

        Returns:
            Template: SPARQL template if available, otherwise None.
        """
        queries = [template for template in templates if template.name == "SPARQL"]
        return queries[0] if len(queries) == 1 else None

    def extract_queries(self):
        """
        Extract all queries from the Wikidata examples page.
        """
        wikitext = self.get_examples_wikitext()
        parsed = wtp.parse(wikitext)
        for section in parsed.sections:
            named_query = self.extract_query_from_section(section)
            if named_query:
                self.named_query_list.queries.append(named_query)

    def save_to_json(self, file_path: str = "/tmp/wikidata-examples.json"):
        """
        Save the NamedQueryList to a JSON file.

        Args:
           file_path (str): Path to the JSON file.
        """
        self.named_query_list.save_to_json_file(file_path, indent=2)

    def store_queries(self):
        """
        Store the named queries into the database.

        """
        self.nqm.store_named_query_list(self.named_query_list)
