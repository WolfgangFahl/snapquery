"""
Created on 2024-05-04
Author: tholzheim
"""
import pprint
import re
import requests
import wikitextparser as wtp
from wikitextparser import Section, Template
from snapquery.wd_short_url import ShortUrl
from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet
from typing import List

class WikipediaQueryExtractor:
    """
    A class to handle the extraction and management
    of SPARQL queries from a Wikipedia page.
    """

    def __init__(self, 
            nqm: NamedQueryManager,
            base_url: str,
            domain: str,
            namespace: str,
            target_graph_name: str,
            template_name:str ="SPARQL" # https://en.wikipedia.org/wiki/Template:SPARQL) - if None seek for short-urls
        ): 
        """
        Constructor
        """
        self.nqm = nqm
        self.base_url = base_url
        self.domain = domain
        self.namespace = namespace
        self.target_graph_name = target_graph_name
        self.template_name=template_name
        self.named_query_list = NamedQuerySet(
            domain=self.domain,
            namespace=self.namespace,
            target_graph_name=self.target_graph_name
        )

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
    
    def extract_query_from_wiki_markup(self,
        title:str,
        markup:str,
        sparql:str)->NamedQuery:
        """
        
        """
        desc = self.sanitize_text(markup)
        if desc:
            # Remove section headers
            desc = re.sub(r"\n*={2,4}.*?={2,4}\n*", "", desc)
        title = self.sanitize_text(title)    
        named_query = NamedQuery(
                domain=self.domain,
                namespace=self.namespace,
                name=title,
                title=title,
                description=desc,
                url=self.base_url,
                sparql=sparql,
            )
        return named_query
      

    def extract_queries_from_wiki_markup(self,markup:str)->List[NamedQuery]:
        """
        """
        named_queries=[]
        #Matches entire lines containing a short URL
        pattern = r"^(.*?)(https?://w\.wiki/\S+)(.*)$"
        matches = re.findall(pattern, markup, re.MULTILINE)

        for pre_text, short_url, post_text in matches:
            pre_text = pre_text.strip()
            post_text = post_text.strip()
            description = f"{pre_text} {post_text}".strip()
            short_url_instance = ShortUrl(short_url=short_url)
            sparql_query = short_url_instance.read_query()
            if sparql_query:
                title=short_url_instance.name
                markup=description
                query = self.extract_query_from_wiki_markup(title,markup, sparql_query)
                named_queries.append(query)
        return named_queries
                
    def extract_queries_from_section(self, section: Section) -> List[NamedQuery]:
        """
        Extract named queries from section.

        Args:
            section (Section): Wikitext section containing a SPARQL query.

        Returns:
            List[NamedQuery]: Extracted named queries.
        """
        named_queries=[]
        if self.template_name:
            template = self.get_template(section.templates)
            if template:
                sparql=template.arguments[0].value
                if sparql:
                    query=self.extract_query_from_wiki_markup(section.title,markup=section.plain_text(),sparql=sparql)
                    named_queries.append(query)
        else:
            markup = section.plain_text()
            queries=self.extract_queries_from_wiki_markup(markup)
            named_queries.extend(queries)
        return named_queries


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

    def extract_queries(self,wikitext:str=None):
        """
        Extract all queries from the base_url page.
        """
        if wikitext is None:
            wikitext = self.get_wikitext()
        parsed = wtp.parse(wikitext)
        for section in parsed.sections:
            named_queries = self.extract_queries_from_section(section)
            self.named_query_list.queries.extend(named_queries)

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