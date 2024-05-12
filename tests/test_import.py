"""
Created on 2024-05-05

@author: wf
"""
import glob
import json
import os
import tempfile

from ngwidgets.basetest import Basetest

from snapquery.qimport import QueryImport
from snapquery.snapquery_core import NamedQueryManager
from snapquery.wd_short_url import ShortUrl


class TestImport(Basetest):
    """
    test importing  named queries
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testSamplesImports(self):
        """
        test importing the samples
        """
        with tempfile.NamedTemporaryFile() as tmpfile:
            nqm = NamedQueryManager.from_samples(db_path=tmpfile.name)
            qimport = QueryImport(nqm=nqm)
            for json_file in glob.glob(os.path.join(nqm.samples_path, "*.json")):
                with_store = True
                show_progress = self.debug
                nq_list = qimport.import_from_json_file(
                    json_file, with_store, show_progress
                )
                if "ceur" in json_file:
                    json_file_name = os.path.basename(json_file)
                    output_path = os.path.join("/tmp", json_file_name)
                    nq_list.save_to_json_file(output_path, indent=2)
                    pass

    def testImport(self):
        """
        Test importing named queries.
        """
        qimport = QueryImport()
        # Create a temporary JSON file to test the import function
        sample_data = {
            "name": "ceur-ws",
            "queries": [
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
        short_url=ShortUrl("https://w.wiki/6UCU")
        query = short_url.read_query()
        if self.debug:
            print(query)
        self.assertTrue("Q0.1" in query)
