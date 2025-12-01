"""
Created on 2024-05-05

@author: wf
"""

import json

from ngwidgets.basetest import Basetest

from snapquery.qimport import QueryImport
from snapquery.wd_short_url import ShortUrl


class TestImport(Basetest):
    """
    test importing  named queries

    the samples import is now tested as part of  TestQueryName
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testImport(self):
        """
        Test importing named queries.
        """
        qimport = QueryImport()
        # Create a temporary JSON file to test the import function
        sample_data = {
            "domain": "ceur-ws.org",
            "namespace": "challenge",
            "target_graph_name": "wikidata",
            "queries": [
                {
                    "domain": "ceur-ws.org",
                    "namespace": "challenge",
                    "name": "AllVolumes",
                    "title": "All [[Concept:Proceedings|proceedings]]",
                    "description": "List all proceedings",
                    "url": "https://w.wiki/6UCU",
                },
                {
                    "domain": "ceur-ws.org",
                    "namespace": "challenge",
                    "name": "LocationOfEvents",
                    "title": "Locations of all CEUR-WS proceedings [[Concept:Proceedings|proceedings]] [[Concept:Event|events]]",
                    "description": "Map of all CEUR-WS event locations",
                    "url": "https://w.wiki/8gRw",
                },
            ],
        }
        json_file = "/tmp/sample_ceur-ws_queries.json"
        with open(json_file, "w") as f:
            json.dump(sample_data, f, indent=2)

        nq_list = qimport.import_from_json_file(json_file)
        queries = nq_list.queries
        for query in queries:
            if self.debug:
                print(query)

        self.assertEqual(len(queries), 2)
        self.assertTrue(any(q.name == "AllVolumes" for q in queries))
        self.assertTrue(any(q.name == "LocationOfEvents" for q in queries))

    def testReadFromShortUrl(self):
        """
        test reading from a short url
        """
        short_url = ShortUrl("https://w.wiki/6UCU")
        query = short_url.read_query()
        if self.debug:
            print(query)
        self.assertTrue("Q0.1" in query)

    def testImportFromShortUrl(self):
        """
        test importing a named query from a short url
        """
        short_url = ShortUrl("https://w.wiki/6UCU")
        qimport = QueryImport()
        nq = qimport.read_from_short_url(short_url, domain="wikidata.org", namespace="short_url")
        self.assertEqual("6UCU", nq.name)
        pass
