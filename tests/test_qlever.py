"""
Created on 2024-06-19

@author: wf
"""
from ngwidgets.basetest import Basetest
from osprojects.osproject import OsProject,Ticket
import re
import unittest
from typing import List

class QLever:
    """
    handle https://github.com/ad-freiburg/qlever specifics
    """
    
    def __init__(self):
        self.url = "https://github.com/ad-freiburg/qlever"
        # Regex pattern to find URLs starting with the specified prefix
        self.wd_url_pattern = re.compile(r'https://qlever\.cs\.uni-freiburg\.de/wikidata\S*')

    def wd_urls_for_ticket(self,ticket:Ticket)->List[str]:
        """
        Extracts and returns all URLs from a ticket's body that match the specified pattern.
        """
        extracted_urls = []
        # Extract and print URLs from the ticket body
        if ticket.body:
            found_urls = self.wd_url_pattern.findall(ticket.body)
            extracted_urls.extend(found_urls)  # Add found URLs to the list
        return extracted_urls
         

class TestQLever(Basetest):
    """
    get QLever related example queries
    """
    
    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.qlever=QLever()

    @unittest.skipIf(Basetest.inPublicCI(), "avoid github rate limit")
    def testGitHub(self):
        """
        Retrieve queries from GitHub tickets, specifically looking for URLs starting with
        'https://qlever.cs.uni-freiburg.de/wikidata' in the ticket bodies.
        """
       
        osp = OsProject.fromUrl(self.qlever.url)
        #limit = 50
        limit=None
        tickets = osp.getAllTickets(limit=limit)
        if self.debug:
            print(f"Found {len(tickets)} tickets")
      
        wd_urls_4tickets = {}  # To store all extracted URLs

        for i, ticket in enumerate(tickets):
            found_urls = self.qlever.wd_urls_for_ticket(ticket)
            if found_urls:
                wd_urls_4tickets[ticket] = found_urls
                if self.debug:
                    print(f"{i:4} {ticket.title} ... {len(found_urls)} URLs found")

        extracted_urls = sum(wd_urls_4tickets.values(), [])
        if self.debug:
            print(f"Total URLs extracted: {len(extracted_urls)}")
            for url in set(extracted_urls):
                print(f"Unique URL: {url}")

        self.assertTrue(extracted_urls, "No URLs matching the specified pattern were found.")

        
        
