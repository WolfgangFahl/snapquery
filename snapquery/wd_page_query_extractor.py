"""
Created on 2024-05-04
Refactored on 2024-05-22
Author: tholzheim
Refactored on 2025-04-12
support progress bar via iterator

This module provides the WikidataQueryExtractor class, which is responsible for
parsing MediaWiki page content to extract SPARQL queries. It supports extracting
queries from 'short url' blocks (w.wiki) and explicit SPARQL templates.
"""

import logging
import pprint
import re
from typing import List, Optional

import wikitextparser as wtp
from wikitextparser import Section, Template

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet, QueryName
from snapquery.wd_short_url import ShortUrl, Wikidata


class WikidataQueryExtractor:
    """
    A class to handle the extraction of SPARQL queries from a Wikidata MediaWiki page content.

    It parses the wikitext to find SPARQL queries embedded either via templates
    (e.g. {{SPARQL|query=...}}) or via `w.wiki` short URLs.
    """

    # Regex to clean up <translate> tags often found in localized pages
    RE_TRANSLATE_TAGS = re.compile(r"<translate>(.*?)<\/translate>", flags=re.DOTALL)
    RE_TRANS_COMMENT = re.compile(r"<!--T:\d+-->")

    # Regex to handle section headers cleanup
    RE_SECTION_HEADER = re.compile(r"\n*={2,4}.*?={2,4}\n*")

    # Regex to find blocks of text containing a w.wiki short URL
    # Captures: (pre-text, short-url, post-text)
    RE_SHORT_URL_BLOCK = re.compile(
        r"(.*?)(https?://w\.wiki/\S+)(.*?)(?=https?://w\.wiki/|\Z)", re.DOTALL | re.MULTILINE
    )

    def __init__(
        self,
        nqm: NamedQueryManager,
        base_url: str,
        domain: str,
        namespace: str,
        target_graph_name: str,
        template_name: Optional[str] = "SPARQL",
        debug: bool = False,
    ):
        """
        Initialize the extractor.

        Args:
            nqm (NamedQueryManager): The manager to store/process query names.
            base_url (str): The URL of the wiki page to extract from.
            domain (str): The domain of the wiki (e.g., 'wikidata.org').
            namespace (str): A logical namespace for the queries (e.g., 'examples').
            target_graph_name (str): The target graph identifier.
            template_name (Optional[str]): The name of the template hosting SPARQL queries.
                                           Defaults to "SPARQL". If None, looks for Short URLs.
            debug (bool): If True, enables verbose logging to stdout.
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
        self.errors: List[str] = []

    def log(self, message: str, is_error: bool = False):
        """
        Log a message to stdout (if debug is True) and to the internal logger.

        Args:
            message (str): The message to log.
            is_error (bool): If True, logs as warning and tracks in self.errors.
        """
        if self.debug:
            print(message)
        if is_error:
            self.logger.warning(message)
            self.errors.append(message)
        else:
            self.logger.info(message)

    def sanitize_text(self, text: str) -> str:
        """
        Remove translation tags and comments from the text to get clean descriptions.

        Args:
            text (str): The raw wikitext snippet.

        Returns:
            str: The sanitized text.
        """
        if not text:
            return ""
        text = self.RE_TRANSLATE_TAGS.sub(r"\1", text)
        text = self.RE_TRANS_COMMENT.sub("", text)
        return text.strip()

    def create_named_query(self, title: str, markup: str, sparql: str, url: Optional[str] = None) -> NamedQuery:
        """
        Factory method to create a NamedQuery object.

        Args:
            title (str): The title of the query.
            markup (str): The description text surrounding the query.
            sparql (str): The actual SPARQL code.
            url (Optional[str]): The source URL (specific anchor or short URL).
                                 Defaults to base_url + anchor if None.

        Returns:
            NamedQuery: The populated query object.
        """
        desc = self.sanitize_text(markup)
        if desc:
            desc = self.RE_SECTION_HEADER.sub("", desc).strip()

        title = self.sanitize_text(title)

        if url is None:
            # Create a default anchor-based URL if a specific short URL isn't available
            anchor = title.replace(" ", "_")
            url = f"{self.base_url}#{anchor}"

        return NamedQuery(
            domain=self.domain,
            namespace=self.namespace,
            name=title,
            title=title,
            description=desc,
            url=url,
            sparql=sparql,
        )

    def extract_queries_from_wiki_markup(self, markup: str) -> None:
        """
        Parse raw wiki markup to find 'w.wiki' short URLs, resolve them to get SPARQL,
        and add them to the query list.

        Args:
            markup (str): The wikimarkup content of a section.
        """
        matches = self.RE_SHORT_URL_BLOCK.findall(markup)

        for pre_text, short_url, post_text in matches:
            self.log(f"Processing short URL: {short_url}")

            pre_text = pre_text.strip()
            post_text = post_text.strip()
            # Combine surrounding text to form a description
            description = f"{pre_text} {post_text}".strip()

            short_url_instance = ShortUrl(short_url=short_url)
            title = short_url_instance.name

            # check if query already exists to avoid duplicates
            query_name = QueryName(name=title, namespace=self.namespace, domain=self.domain)
            if query_name.query_id in self.named_query_list._query_dict:
                self.log(f"Query {title} ({query_name.query_id}) already exists. Skipping.", is_error=True)
                continue

            # This handles fetching the SPARQL from the short URL redirection
            sparql_query = short_url_instance.read_query()

            if short_url_instance.error:
                self.log(f"Error reading query from {short_url}: {short_url_instance.error}", is_error=True)
                continue

            if sparql_query:
                query = self.create_named_query(
                    title=title, markup=description, sparql=sparql_query, url=short_url_instance.short_url
                )
                self.named_query_list.add(query)
                self.log(f"Added query: {title}")
            else:
                self.log(f"No SPARQL content found for {short_url}", is_error=True)

    def extract_queries_from_section(self, section: Section) -> None:
        """
        Process a specific section of the parsed wikitext.
        If a template_name is defined, it looks for that template.
        Otherwise, it falls back to looking for short URLs in the plain text.

        Args:
            section (Section): A wikitextparser Section object.
        """
        if self.template_name:
            template = self.get_template(section.templates)
            if template:
                if template.arguments:
                    # Assuming the first argument contains the query text
                    sparql = template.arguments[0].value
                    if sparql:
                        query = self.create_named_query(title=section.title, markup=section.plain_text(), sparql=sparql)
                        self.named_query_list.add(query)
            return

        # Fallback to parsing text for Short URLs
        markup = section.plain_text()
        self.extract_queries_from_wiki_markup(markup)

    def get_template(self, templates: List[Template]) -> Optional[Template]:
        """
        Filter a list of templates to find the one matching self.template_name.
        """
        matching = [t for t in templates if t.name.strip() == self.template_name]
        return matching[0] if len(matching) == 1 else None

    def fetch_wikitext(self) -> Optional[str]:
        """
        Fetch the wikitext content using the configured base_url.

        Returns:
            Optional[str]: The raw wikitext, or None on failure.
        """
        self.log(f"Fetching wikitext from {self.base_url}...")
        wd = Wikidata()
        wikitext = wd.get_wikitext(self.base_url)

        if not wikitext:
            self.log(f"Failed to retrieve wikitext from {self.base_url}", is_error=True)
            return None
        return wikitext

    def get_sections(self, wikitext: str) -> List[Section]:
        """
        Parse wikitext into sections.

        Args:
            wikitext (str): Raw wikitext.

        Returns:
            List[Section]: List of wikitextparser sections.
        """
        parsed = wtp.parse(wikitext)
        return parsed.sections

    def extract_queries(self, wikitext: Optional[str] = None):
        """
        Main entry point for extraction.

        Behavior:
        1. If `wikitext` is provided (e.g., from a local file during testing),
           it processes that string directly.
        2. If `wikitext` is None, it utilizes the Wikidata() helper to fetch
           the content from `self.base_url`.

        Args:
            wikitext (Optional[str]): Raw wikitext content. If None, fetches from URL.
        """
        if wikitext is None:
            wikitext = self.fetch_wikitext()
            if not wikitext:
                return

        sections = self.get_sections(wikitext)
        for section in sections:
            self.extract_queries_from_section(section)

        if not self.debug and self.errors:
            self.logger.info(
                f"Encountered {len(self.errors)} errors during extraction. Set debug=True for more details."
            )

    def save_to_json(self, file_path: str):
        """
        Serialize the extracted named queries to a JSON file.
        """
        self.named_query_list.save_to_json_file(file_path, indent=2)

    def store_queries(self):
        """
        Store the extracted queries into the main NamedQueryManager instance.
        """
        self.nqm.store_named_query_list(self.named_query_list)

    def show_queries(self):
        """
        Debug helper to print extracted queries to stdout.
        """
        for query in self.named_query_list.queries:
            pprint.pprint(query)
        print(f"Found {len(self.named_query_list.queries)} queries")

    def show_errors(self):
        """
        Debug helper to print runtime errors to stdout.
        """
        print(f"{len(self.errors)} errors:")
        for i, error in enumerate(self.errors, start=1):
            print(f"{i:3}: {error}")
