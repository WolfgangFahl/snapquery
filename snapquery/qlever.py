"""
Created on 2024-06-20

@author: wf
"""

import re
from typing import Dict, List

from bs4 import BeautifulSoup
from osprojects.osproject import OsProject, Ticket
from tqdm import tqdm

from snapquery.snapquery_core import NamedQuery, NamedQuerySet
from snapquery.wd_short_url import ShortUrl


class QLeverUrl(ShortUrl):
    """
    Handles operations related to QLever short URLs.
    """

    def __init__(self, short_url: str):
        super().__init__(short_url, scheme="https", netloc="qlever.cs.uni-freiburg.de")
        self.sparql = None

    def read_query(self) -> str:
        """
        Read a query from a QLever short URL.
        It follows redirects and parses the HTML to find the query in the textarea.

        Returns:
            str: The SPARQL query extracted from the short URL.
        """
        # Ensure we have the final URL (handles redirects)
        self.fetch_final_url(self.short_url)

        if self.url:
            try:
                # Assuming ShortUrl or its parent has a get_content or similar method.
                # If not, specific request logic would go here.
                # Using get_wikitext as per your snippet pattern, assuming it returns page content.
                text = self.get_wikitext(self.url)
                if text:
                    soup = BeautifulSoup(text, "html.parser")
                    query_element = soup.find("textarea", {"id": "query"})
                    if query_element and query_element.text:
                        self.sparql = query_element.text.strip()
            except Exception as ex:
                self.error = ex
        return self.sparql


class QLever:
    """
    Handle https://github.com/ad-freiburg/qlever specifics
    and interaction with QLever instances.
    """

    def __init__(
        self,
        with_progress: bool = True,
        debug: bool = False,
    ):
        """
        constructor
        """
        self.url = "https://github.com/ad-freiburg/qlever"
        self.with_progress = with_progress
        self.debug = debug
        # Regex pattern to find URLs starting with the specified prefix
        self.wd_url_pattern = re.compile(r"https://(?:qlever\.cs\.uni-freiburg\.de|qlever\.dev)/wikidata/[A-Za-z0-9]+")
        self.osproject = OsProject.fromUrl(self.url)

    def wd_urls_for_ticket(self, ticket: Ticket) -> List[str]:
        """
        Extracts and returns all URLs from a ticket's body and comments
        that match the QLever Wikidata pattern.
        """
        extracted_urls = []

        # Extract URLs from the ticket body
        if ticket.body:
            found_urls = self.wd_url_pattern.findall(ticket.body)
            extracted_urls.extend(found_urls)

        # Fetch and extract URLs from comments
        comments = self.osproject.getComments(ticket.number)
        for comment in comments:
            if "body" in comment:
                found_urls = self.wd_url_pattern.findall(comment["body"])
                extracted_urls.extend(found_urls)

        # distinct list
        ticket_urls = list(set(extracted_urls))
        return ticket_urls

    def get_issues_query_set(self, limit: int = None, progress: bool = False) -> NamedQuerySet:
        """
        Orchestrates the retrieval of tickets, extraction of URLs,
        resolving of SPARQL queries, and creation of a NamedQuerySet.

        Args:
            limit (int): Max number of tickets to process.
            progress (bool): Whether to show a CLI progress bar.

        Returns:
            NamedQuerySet: The populated query set.
        """
        # Get the full dictionary
        tickets_map = self.osproject.getAllTickets(limit=limit)
        items_iterable = tickets_map.items()

        if progress:
            iterator = tqdm(
                items_iterable, total=len(tickets_map), desc="Scanning tickets for QLever URLs", unit="ticket"
            )
        else:
            iterator = items_iterable

        ticket_dict = {}

        # 1. Scan tickets for URLs
        for i, (t_id, ticket) in enumerate(iterator):
            msg = f"fetching short urls for ticket {i}:#{t_id} {ticket.title}"
            if self.debug:
                print(msg)
            urls = self.wd_urls_for_ticket(ticket)
            if urls:
                ticket_dict[ticket] = urls

        # 2. Convert to NamedQuerySet
        # (This resolves the short URLs to actual SPARQL)
        nq_set = self.named_queries_for_tickets(ticket_dict)
        return nq_set

    def named_queries_for_tickets(self, ticket_dict: Dict[Ticket, List[str]]) -> NamedQuerySet:
        """
        Create named queries for each ticket's extracted URLs.

        Args:
            ticket_dict (dict): Dictionary mapping tickets to a list of URLs.

        Returns:
            NamedQuerySet: A set of named queries generated from the URLs.
        """
        named_query_set = NamedQuerySet(
            domain="qlever.dev",
            namespace="issues.wikidata",
            target_graph_name="wikidata",
        )

        total_urls = sum(len(urls) for urls in ticket_dict.values())

        # We might want progress here if there are many URLs to resolve
        if self.with_progress and total_urls > 0:
            pbar = tqdm(total=total_urls, desc="Resolving QLever URLs", unit="url")
        else:
            pbar = None

        for ticket, urls in ticket_dict.items():
            for i, url in enumerate(urls, 1):
                # Resolve the Short URL
                qlever_url = QLeverUrl(url)
                sparql = qlever_url.read_query()

                if sparql:
                    # Construct the NamedQuery
                    query = NamedQuery(
                        domain=named_query_set.domain,
                        name=f"Issue{ticket.number}_query{i}",
                        namespace=named_query_set.namespace,
                        url=url,
                        sparql=sparql,
                        title=f"QLever Issue #{ticket.number} Query {i}",
                        description=ticket.title,
                        comment=f"Source: Ticket {ticket.url}, QLever Link: {url}",
                    )
                    named_query_set.queries.append(query)

                if pbar:
                    pbar.update(1)

        if pbar:
            pbar.close()

        return named_query_set
