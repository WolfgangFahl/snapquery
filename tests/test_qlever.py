"""
Created on 2024-06-19

@author: wf
"""
from tqdm import tqdm
from ngwidgets.basetest import Basetest
from osprojects.osproject import OsProject,Ticket
import re
import unittest
from typing import List
from snapquery.wd_short_url import ShortUrl
from snapquery.snapquery_core import NamedQuery, NamedQueryList
from bs4 import BeautifulSoup
import requests

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
                soup = BeautifulSoup(response.content, 'html.parser')
                query_element = soup.find('pre', {'id': 'query'})
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
        self.wd_url_pattern = re.compile(r'https://qlever\.cs\.uni-freiburg\.de/wikidata/[A-Za-z0-9]+')
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
            found_urls = self.wd_url_pattern.findall(comment['body'])
            extracted_urls.extend(found_urls)

        return extracted_urls
    
    def named_queries_for_tickets(self, ticket_dict):
        """
        Create named queries for each ticket's extracted URLs.

        Args:
            ticket_dict (dict): Dictionary mapping tickets to a list of URLs.

        Returns:
            NamedQueryList: A list of named queries generated from the URLs.
        """
        named_query_list = NamedQueryList(name="QLever Queries")
        for ticket, urls in ticket_dict.items():
            for i,url in enumerate(urls):
                # Assuming URLs are like 'https://qlever.cs.uni-freiburg.de/wikidata/iTzJwQ'
                # Customizing ShortUrl instance for QLever specific URLs
                short_url_handler = QLeverUrl(url)
                short_url_handler.read_query()
                if short_url_handler.sparql:
                    # Example placeholder logic to create a NamedQuery for each URL
                    query = NamedQuery(
                        name=f"Ticket#{ticket.number}-query{i}",
                        namespace="QLever",
                        url=url,
                        sparql=short_url_handler.sparql,
                        title=f"QLever github issue #{ticket.number}-query{i}",
                        description=ticket.title,
                        comment=f"See {url}"
                    )
                    named_query_list.queries.append(query)
        return named_query_list
         

class TestQLever(Basetest):
    """
    get QLever related example queries
    """
    
    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.qlever=QLever()
        
    def test_qlever_url(self):
        """
        Test extracting SPARQL query from a QLever short URL.
        """
        url = "https://qlever.cs.uni-freiburg.de/wikidata/h6p82D"
        qlever_url = QLeverUrl(url)
        sparql_query = qlever_url.read_query()
        if self.debug:
            print(sparql_query)
        self.assertTrue(sparql_query, "Failed to extract SPARQL query from QLever URL.")


    @unittest.skipIf(Basetest.inPublicCI(), "avoid github rate limit")
    def testGitHub(self):
        """
        Retrieve queries from GitHub tickets, specifically looking for URLs starting with
        'https://qlever.cs.uni-freiburg.de/wikidata' in the ticket bodies.
        """
        limit = 50
        #limit=None
        tickets = self.qlever.osproject.getAllTickets(limit=limit)
        if self.debug:
            print(f"Found {len(tickets)} tickets")
      
        wd_urls_4tickets = {}  # To store all extracted URLs
        count=0
        # Conditionally use tqdm based on with_progress
        if self.qlever.with_progress:
            ticket_iterator = tqdm(enumerate(tickets), desc="Processing tickets", unit="ticket")
        else:
            ticket_iterator = enumerate(tickets)
        
        for i, ticket in ticket_iterator:

            found_urls = self.qlever.wd_urls_for_ticket(ticket)
            if found_urls:
                wd_urls_4tickets[ticket] = found_urls
                count+=len(found_urls)
  
        if self.debug:
            print(f"Total URLs extracted: {count}")
            for ticket, urls in wd_urls_4tickets.items():
                print(f"{ticket.number} {ticket.title}")
                for url in urls:
                    print(f"\t{url}")
            # Assertion to ensure that at least one URL was found in any ticket
        self.assertTrue(wd_urls_4tickets, "No URLs matching the specified pattern were found.")

        nq_list=self.qlever.named_queries_for_tickets(wd_urls_4tickets)
        nq_list.save_to_json_file("/tmp/qlever.json", indent=2)
        
        
