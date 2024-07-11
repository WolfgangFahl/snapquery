"""
Created on 2024-06-20

@author: wf
"""
import re
from typing import List

import requests
from bs4 import BeautifulSoup
from osprojects.osproject import OsProject, Ticket

from snapquery.snapquery_core import NamedQuery, NamedQuerySet
from snapquery.wd_short_url import ShortUrl


class QLeverUrl(ShortUrl):
    """
    Handles operations related to QLever short URLs.
    """

    def __init__(self, short_url: str):
        super().__init__(short_url, scheme="https", netloc="qlever.cs.uni-freiburg.de")

    def read_query(self) -> str:
        """
        Read a query from a QLever short URL.

        Returns:
            str: The SPARQL query extracted from the short URL.
        """
        self.fetch_final_url()
        if self.url:
            try:
                response = requests.get(self.url)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, "html.parser")
                query_element = soup.find("textarea", {"id": "query"})
                if query_element and query_element.text:
                    self.sparql = query_element.text.strip()
            except Exception as ex:
                self.error = ex
        return self.sparql


class QLever:
    """
    handle https://github.com/ad-freiburg/qlever specifics
    """

    def __init__(self, with_progress=True):
        self.url = "https://github.com/ad-freiburg/qlever"
        self.with_progress = with_progress
        # Regex pattern to find URLs starting with the specified prefix
        self.wd_url_pattern = re.compile(r"https://qlever\.cs\.uni-freiburg\.de/wikidata/[A-Za-z0-9]+")
        self.osproject = OsProject.fromUrl(self.url)

    def wd_urls_for_ticket(self, ticket: Ticket) -> List[str]:
        """
        Extracts and returns all URLs from a ticket's body and comments that match the specified pattern.
        """
        extracted_urls = []

        # Extract URLs from the ticket body
        if ticket.body:
            found_urls = self.wd_url_pattern.findall(ticket.body)
            extracted_urls.extend(found_urls)

        # Fetch and extract URLs from comments
        comments = self.osproject.ticketSystem.getComments(self.osproject, ticket.number)
        for comment in comments:
            found_urls = self.wd_url_pattern.findall(comment["body"])
            extracted_urls.extend(found_urls)

        return extracted_urls

    def named_queries_for_tickets(self, ticket_dict):
        """
        Create named queries for each ticket's extracted URLs.

        Args:
            ticket_dict (dict): Dictionary mapping tickets to a list of URLs.

        Returns:
            NamedQuerySet: A set of named queries generated from the URLs.
        """
        named_query_set = NamedQuerySet(
            domain="qlever.cs.uni-freiburg.de",
            namespace="issues.wikidata",
            target_graph_name="wikidata",
        )
        for ticket, urls in ticket_dict.items():
            for i, url in enumerate(urls, 1):
                # Assuming URLs are like 'https://qlever.cs.uni-freiburg.de/wikidata/iTzJwQ'
                # Customizing ShortUrl instance for QLever specific URLs
                short_url_handler = QLeverUrl(url)
                short_url_handler.read_query()
                if short_url_handler.sparql:
                    # Example placeholder logic to create a NamedQuery for each URL
                    query = NamedQuery(
                        domain=named_query_set.domain,
                        name=f"Issue{ticket.number}-query{i}",
                        namespace=named_query_set.namespace,
                        url=url,
                        sparql=short_url_handler.sparql,
                        title=f"QLever github issue #{ticket.number}-query{i}",
                        description=ticket.title,
                        comment=f"See ticket {ticket.url} and query {url}",
                    )
                    named_query_set.queries.append(query)
        return named_query_set
