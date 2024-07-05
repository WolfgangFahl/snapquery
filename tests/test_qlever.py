"""
Created on 2024-06-19

@author: wf
"""
import os
import unittest

from ngwidgets.basetest import Basetest
from tqdm import tqdm

from snapquery.qlever import QLever, QLeverUrl
from snapquery.snapquery_core import NamedQuerySet, NamedQuery


class TestQLever(Basetest):
    """
    get QLever related example queries
    """

    def setUp(self, debug=False, profile=True):
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
        
    def named_queries_for_performance_evaluation(self, queries):
        named_query_set = NamedQuerySet(
            domain="qlever.cs.uni-freiburg.de",
            namespace="performance-dblp",
            target_graph_name="dblp"
        )
        for name, details in queries.items():
            qlever_url = QLeverUrl(details['url'])
            sparql = qlever_url.read_query()
            query = NamedQuery(
                domain=named_query_set.domain,
                name=name,
                namespace=named_query_set.namespace,
                url=details['url'],
                sparql=sparql,
                title=f"{name}",
                description=f"Performance evaluation query: {name}",
                comment=f"{details['comment']} - see https://github.com/ad-freiburg/qlever/wiki/QLever-performance-evaluation-and-comparison-to-other-SPARQL-engines"
            )
            named_query_set.queries.append(query)
        return named_query_set

    def testPerformanceEvaluation(self):
        """
        Test creating a json file for the 
        QLever Performance Evaluation
        https://github.com/ad-freiburg/qlever/wiki/QLever-performance-evaluation-and-comparison-to-other-SPARQL-engines
        """
        queries = {
            "All papers published in SIGIR": {
                "url": "https://qlever.cs.uni-freiburg.de/dblp/m3osZX",
                "comment": "Two simple joins, nothing special"
            },
            "Number of papers by venue": {
                "url": "https://qlever.cs.uni-freiburg.de/dblp/weowtF",
                "comment": "Scan of a single predicate with GROUP BY and ORDER BY"
            },
            "Author names matching REGEX": {
                "url": "https://qlever.cs.uni-freiburg.de/dblp/bVZBoH",
                "comment": "Joins, GROUP BY, ORDER BY, FILTER REGEX"
            },
            "All papers in DBLP until 1940": {
                "url": "https://qlever.cs.uni-freiburg.de/dblp/Rd9ixQ",
                "comment": "Three joins, a FILTER, and an ORDER BY"
            },
            "All papers with their title": {
                "url": "https://qlever.cs.uni-freiburg.de/dblp/WzABwD",
                "comment": "Simple, but must materialize large result (problematic for many SPARQL engines)"
            },
            "All predicates ordered by size": {
                "url": "https://qlever.cs.uni-freiburg.de/dblp/8R9a3u",
                "comment": "Conceptually requires a scan over all triples, but huge optimization potential"
            }
        }
        named_query_set = self.named_queries_for_performance_evaluation(queries)
        
        self.assertEqual(len(named_query_set.queries), len(queries), 
                         "Number of generated named queries doesn't match input queries")
    
        for query in named_query_set.queries:
            self.assertIn(query.name, queries.keys(), 
                          f"Generated query name {query.name} not found in input queries")
            self.assertEqual(query.url, queries[query.name]['url'], 
                             f"URL mismatch for query {query.name}")
            self.assertTrue(query.sparql, f"No SPARQL content for query {query.name}")
            self.assertIn(queries[query.name]['comment'], query.comment, 
                          f"Comment mismatch for query {query.name}")
    
        json_file = "/tmp/qlever_performance.json"
        named_query_set.save_to_json_file(json_file, indent=2)
        
        self.assertTrue(os.path.exists(json_file), f"JSON file {json_file} was not created")
    
        if self.debug:
            print(f"Created JSON file: {json_file}")
            for query in named_query_set.queries:
                print(f"Query: {query.name}")
                print(f"URL: {query.url}")
                print(f"Comment: {query.comment}")
                print(f"SPARQL (first 100 chars): {query.sparql[:100]}...")
                print()
    
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
