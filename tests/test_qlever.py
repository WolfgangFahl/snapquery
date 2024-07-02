"""
Created on 2024-06-19

@author: wf
"""
import unittest

from ngwidgets.basetest import Basetest
from tqdm import tqdm

from snapquery.qlever import QLever, QLeverUrl


class TestQLever(Basetest):
    """
    get QLever related example queries
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.qlever = QLever()

    @unittest.skipIf(Basetest.inPublicCI(), "avoid github rate limit")
    def test_qlever_url(self):
        """
        Test extracting SPARQL query from a QLever short URL.
        """
        url = "https://qlever.cs.uni-freiburg.de/wikidata/h6p82D"
        qlever_url = QLeverUrl(url)
        sparql_query = qlever_url.read_query()
        expected = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
SELECT * WHERE {
  ?person wdt:P31 wd:Q5 .
  ?pesron wdt:P106 ?occupation .
}"""
        if self.debug:
            print(sparql_query)
        self.assertTrue(sparql_query, "Failed to extract SPARQL query from QLever URL.")
        self.assertEqual(expected, sparql_query)

    @unittest.skipIf(Basetest.inPublicCI(), "avoid github rate limit")
    def testGitHub(self):
        """
        Retrieve queries from QLever GitHub tickets,
        specifically looking for URLs starting with
        'https://qlever.cs.uni-freiburg.de/wikidata'
        in the ticket bodies and comments.
        """
        # limit = 50
        limit = None
        tickets = self.qlever.osproject.getAllTickets(limit=limit)
        if self.debug:
            print(f"Found {len(tickets)} tickets")

        wd_urls_4tickets = {}  # To store all extracted URLs
        count = 0
        # Conditionally use tqdm based on with_progress
        if self.qlever.with_progress:
            ticket_iterator = tqdm(
                enumerate(tickets), desc="Processing tickets", unit="ticket"
            )
        else:
            ticket_iterator = enumerate(tickets)

        for _i, ticket in ticket_iterator:

            found_urls = self.qlever.wd_urls_for_ticket(ticket)
            if found_urls:
                wd_urls_4tickets[ticket] = found_urls
                count += len(found_urls)

        if self.debug:
            print(f"Total URLs extracted: {count}")
            for ticket, urls in wd_urls_4tickets.items():
                print(f"{ticket.number} {ticket.title}")
                for url in urls:
                    print(f"\t{url}")
            # Assertion to ensure that at least one URL was found in any ticket
        self.assertTrue(
            wd_urls_4tickets, "No URLs matching the specified pattern were found."
        )

        nq_list = self.qlever.named_queries_for_tickets(wd_urls_4tickets)
        nq_list.save_to_json_file("/tmp/qlever.json", indent=2)
