"""
Created on 2024-05-05

@author: wf
"""
import json

from ngwidgets.basetest import Basetest

from snapquery.qimport import QueryImport
from snapquery.snapquery_core import NamedQueryManager


class TestImport(Basetest):
    """
    test importing  named queries
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testImport(self):
        """
        Test importing named queries.
        """
        qimport = QueryImport()
        # Create a temporary JSON file to test the import function
        sample_data = [
            {
                "namespace": "ceur-ws",
                "name": "AllVolumes",
                "title": "All [[Concept:Proceedings|proceedings]]",
                "description": "List all proceedings",
                "url": "https://w.wiki/6UCU",
            },
            {
                "namespace": "ceur-ws",
                "name": "LocationOfEvents",
                "title": "Locations of all CEUR-WS proceedings [[Concept:Proceedings|proceedings]] [[Concept:Event|events]]",
                "description": "Map of all CEUR-WS event locations",
                "url": "https://w.wiki/8gRw",
            },
        ]
        json_file = "/tmp/sample_ceur-ws_queries.json"
        with open(json_file, "w") as f:
            json.dump(sample_data, f)

        queries = qimport.import_from_json_file(json_file)
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
        url = "https://w.wiki/6UCU"
        qimport = QueryImport()
        query = qimport.read_from_short_url(url)
        if self.debug:
            print(query)
        self.assertTrue("Q0.1" in query)
