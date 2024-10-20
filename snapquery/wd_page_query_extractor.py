"""
Created on 2024-05-04
Author: tholzheim
"""

import logging
import pprint
import re
from typing import List

import requests
import wikitextparser as wtp
from wikitextparser import Section, Template

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet, QueryName
from snapquery.wd_short_url import ShortUrl


class WikipediaQueryExtractor:
    """
    A class to handle the extraction and management
    of SPARQL queries from a Wikipedia page.
    """

    def __init__(
        self,
        nqm: NamedQueryManager,
        base_url: str,
        domain: str,
        namespace: str,
        target_graph_name: str,
        template_name: str = "SPARQL",  # https://en.wikipedia.org/wiki/Template:SPARQL) - if None seek for short-urls
        debug: bool = False,
    ):
        """
        Constructor
        """
        self.nqm = nqm
        self.base_url = base_url
        self.domain = domain
        self.namespace = namespace
        self.target_graph_name = target_graph_name
        self.template_name = template_name
        self.debug = debug
        self.logger = logging.getLogger("snapquery.wd_page_extractor.WikipediaQueryExtractor")

        self.named_query_list = NamedQuerySet(
            domain=self.domain, namespace=self.namespace, target_graph_name=self.target_graph_name
        )
        self.errors = []

    def log(self, message: str, is_error: bool = False):
        if self.debug:
            print(message)
        if is_error:
            self.logger.debug(message)
            self.errors.append(message)

    def get_wikitext(self) -> str:
        """
        Get wiki text with SPARQL query examples.

        Returns:
            str: Raw wikitext of the page.
        """
        res = requests.get(f"{self.base_url}?action=raw")
        return res.text

    def sanitize_text(self, text: str) -> str:
        """
        General method to sanitize text by removing translation tags, comments,
        and other non-essential markup.

        Args:
            text (str): The text to be sanitized.

        Returns:
            str: The sanitized text.
        """
        # Remove <translate>...</translate> tags
        text = re.sub(r"<translate>(.*?)<\/translate>", r"\1", text, flags=re.DOTALL)
        # Remove <!--T:...--> tags
        text = re.sub(r"<!--T:\d+-->", "", text)
        # Strip whitespace that might be left at the beginning and end
        text = text.strip()
        return text

    def extract_query_from_wiki_markup(self, title: str, markup: str, sparql: str, url: str = None) -> NamedQuery:
        """
        Extracts a named query from wiki markup.

        This method processes the title, markup, and SPARQL query to create a NamedQuery object.
        It sanitizes the text, removes section headers from the description, and constructs
        a URL that points to the specific section of the Wikipedia page.

        Args:
            title (str): The title of the query section.
            markup (str): The wiki markup text containing the query description.
            sparql (str): The SPARQL query string.
            url(str): the url to assign - if not given derive from base_url and section title

        Returns:
            NamedQuery: A NamedQuery object containing the processed information.

        Note:
            The method sanitizes the title and description, removes section headers from the
            description, and constructs a URL with a section anchor based on the title.
        """
        desc = self.sanitize_text(markup)
        if desc:
            # Remove section headers
            desc = re.sub(r"\n*={2,4}.*?={2,4}\n*", "", desc)
            desc = desc.strip()
        title = self.sanitize_text(title)
        if url is None:
            url = f"{self.base_url}#{title.replace(' ', '_')}"
        named_query = NamedQuery(
            domain=self.domain,
            namespace=self.namespace,
            name=title,
            title=title,
            description=desc,
            url=url,
            sparql=sparql,
        )
        return named_query

    def extract_queries_from_wiki_markup(self, markup: str) -> List[NamedQuery]:
        named_queries = []
        pattern = r"(.*?)(https?://w\.wiki/\S+)(.*?)(?=https?://w\.wiki/|\Z)"
        matches = re.findall(pattern, markup, re.DOTALL | re.MULTILINE)

        for pre_text, short_url, post_text in matches:
            self.log(f"Processing short URL: {short_url}")
            pre_text = pre_text.strip()
            post_text = post_text.strip()
            description = f"{pre_text} {post_text}".strip()
            short_url_instance = ShortUrl(short_url=short_url)

            title = short_url_instance.name
            query_name = QueryName(name=title, namespace=self.namespace, domain=self.domain)

            if query_name.query_id in self.named_query_list._query_dict:
                self.log(f"Query with ID {query_name.query_id} already exists. Skipping.", is_error=True)
                continue

            sparql_query = short_url_instance.read_query()
            if short_url_instance.error:
                self.log(f"Error reading query from {short_url}: {short_url_instance.error}", is_error=True)
                continue

            if sparql_query:
                query = self.extract_query_from_wiki_markup(
                    title=title, markup=description, sparql=sparql_query, url=short_url_instance.short_url
                )
                self.named_query_list.add(query)
                self.log(f"Added query: {title}")
            else:
                self.log(f"No query found for short URL {short_url}", is_error=True)

        if not self.debug and self.errors:
            self.logger.info(
                f"Encountered {len(self.errors)} errors during extraction. Set debug=True for more details."
            )

        return named_queries

    def extract_queries_from_section(self, section: Section):
        """
        Extract named queries from section.

        Args:
            section (Section): Wikitext section containing a SPARQL query.
        """
        if self.template_name:
            template = self.get_template(section.templates)
            if template:
                sparql = template.arguments[0].value
                if sparql:
                    query = self.extract_query_from_wiki_markup(
                        section.title, markup=section.plain_text(), sparql=sparql
                    )
                    self.named_query_list.add(query)
        else:
            markup = section.plain_text()
            self.extract_queries_from_wiki_markup(markup)

    def get_template(self, templates: list[Template]) -> Template:
        """
        Get template from the list of templates.

        Args:
            templates (list[Template]): List of Wikitext templates.

        Returns:
            Template: template if available, otherwise None.
        """
        queries = [template for template in templates if template.name == self.template_name]
        return queries[0] if len(queries) == 1 else None

    def extract_queries(self, wikitext: str = None):
        """
        Extract all queries from the base_url page.
        """
        if wikitext is None:
            wikitext = self.get_wikitext()
        parsed = wtp.parse(wikitext)
        for section in parsed.sections:
            self.extract_queries_from_section(section)

    def save_to_json(self, file_path: str):
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

    def show_queries(self):
        for query in self.named_query_list.queries:
            pprint.pprint(query)
        print(f"Found {len(self.named_query_list.queries)} queries")

    def show_errors(self):
        print(f"{len(self.errors)} errors:")
        for i, error in enumerate(self.errors, start=1):
            print(f"{i:3}:{error}")
