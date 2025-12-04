"""
Created on 2024-05-05

@author: wf
"""

import json
from basemkit.basetest import Basetest

from snapquery.query_set_tool import QuerySetTool
from snapquery.wd_short_url import ShortUrl


class TestQuerySetTool(Basetest):
    """
    test importing and converting named queries

    the samples import is now tested as part of TestQueryName
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testImport(self):
        """
        Test importing named queries (legacy check).
        """
        qimport = QuerySetTool()
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
                    "title": "Locations of all CEUR-WS proceedings",
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
        qimport = QuerySetTool()
        nq = qimport.read_from_short_url(short_url, domain="wikidata.org", namespace="short_url")
        self.assertEqual("6UCU", nq.name)

    def test_infer_format(self):
        """
        Test input format inference logic.
        """
        qt = QuerySetTool()
        self.assertEqual("json", qt.infer_format("test.json"))
        self.assertEqual("yaml", qt.infer_format("test.yaml"))
        self.assertEqual("yaml", qt.infer_format("test.yml"))
        self.assertEqual("auto", qt.infer_format("test.txt"))
        # Force overrides
        self.assertEqual("json", qt.infer_format("test.yaml", "json"))
        self.assertEqual("yaml", qt.infer_format("test.json", "yaml"))

    def test_conversion(self):
        """
        Test the loading and conversion capabilities by round-tripping a dataset.
        """
        qt = QuerySetTool()

        # 1. Create a sample JSON file
        sample_data = {
            "domain": "example.org",
            "namespace": "test",
            "target_graph_name": "wikidata",
            "queries": [
                {
                    "domain": "example.org",
                    "namespace": "test",
                    "name": "Q1",
                    "title": "First Query",
                    "description": "A test query",
                    "sparql": "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
                }
            ]
        }
        src_json = "/tmp/test_convert_src.json"
        dst_yaml = "/tmp/test_convert_dst.yaml"

        with open(src_json, "w") as f:
            json.dump(sample_data, f, indent=2)

        # 2. Convert: Load JSON using tool
        nq_set = qt.load_query_set(src_json)
        self.assertEqual(len(nq_set.queries), 1)
        self.assertEqual(nq_set.queries[0].name, "Q1")

        # 3. Save as YAML (simulating the 'output' part of the command)
        nq_set.save_to_yaml_file(dst_yaml)

        # 4. Verify: Load back YAML
        nq_set_yaml = qt.load_query_set(dst_yaml)
        self.assertEqual(nq_set_yaml.domain, "example.org")
        self.assertEqual(len(nq_set_yaml.queries), 1)
        self.assertEqual(nq_set_yaml.queries[0].sparql, sample_data["queries"][0]["sparql"])

    def test_load_error(self):
        """
        Test behavior when loading invalid files
        """
        qt = QuerySetTool()
        bad_path = "/tmp/bad_data.txt"
        with open(bad_path, "w") as f:
            f.write("This is garbage data")

        # Should raise exception when both JSON and YAML loaders fail
        with self.assertRaises(Exception):
            qt.load_query_set(bad_path)