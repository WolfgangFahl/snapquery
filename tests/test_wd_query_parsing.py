"""
Created on 2024-05-04
@author: tholzheim
"""

import tempfile
import unittest

from basemkit.basetest import Basetest

from snapquery.snapquery_core import NamedQueryManager
from snapquery.wd_page_query_extractor import WikidataQueryExtractor


class TestWikidataQueryParsing(Basetest):
    """
    Test suite for the WikdataQueryExtractor class.
    Verifies that SPARQL queries can be correctly extracted from
    Wiki pages (both via Short URL resolution and direct template parsing).
    """

    def setUp(self, debug=False, profile=True):
        """
        Set up the test environment.
        Initializes a temporary NamedQueryManager and two extractor instances:
        1. lse_extractor: Tests standard wiki page behavior.
        2. wikidata_example_extractor: Tests the official SPARQL examples page.
        """
        Basetest.setUp(self, debug=debug, profile=profile)
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            self.nqm = NamedQueryManager.from_samples(db_path=tmpfile.name)

            self.lse_extractor = WikidataQueryExtractor(
                nqm=self.nqm,
                base_url="https://www.wikidata.org/wiki/Wikidata:WikiProject_LSEThesisProject",
                domain="wikidata.org",
                namespace="WikidataThesisToolkit",
                target_graph_name="wikidata",
                template_name=None,
                debug=self.debug,
            )
            self.wikidata_example_extractor = WikidataQueryExtractor(
                nqm=self.nqm,
                base_url="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples",
                domain="wikidata.org",
                namespace="examples",
                target_graph_name="wikidata",
                debug=self.debug,
            )

    def test_query_extraction(self):
        """
        Test extraction and parsing of queries from Wikidata example page and WikiProject LSEThesisProject page.
        Iterates over the defined extractors and validates query counts.
        """
        wikidata_examples = [(self.wikidata_example_extractor, 389)]  # 302 as of 2024-07-11

        # Optional manual toggle for local testing of LSE extractor
        with_lse = False
        if with_lse:
            wikidata_examples.append((self.lse_extractor, 23))

        for extractor, expected in wikidata_examples:
            with self.subTest(extractor=extractor):
                self._test_extractor(extractor, expected)

    @unittest.skipIf(Basetest.inPublicCI(), "unreliable execution in CI")
    def test_wikidata_thesis_toolkit(self):
        """
        Test the Wikidata Thesis Toolkit extraction using a local file.
        This verifies the logic without relying on network calls to the wiki.
        """
        markup_file = "../snapquery/samples/WikiProject_LSEThesisProject.wiki"

        with open(markup_file, "r") as wikitext_file:
            markup = wikitext_file.read()

        extractor = self.lse_extractor
        # Passing markup explicitly avoids network call in extractor.extract_queries()
        extractor.extract_queries(wikitext=markup)

        if self.debug:
            extractor.show_queries()

        # Verify we found the expected number of queries
        expected = 23
        self.assertGreaterEqual(
            len(extractor.named_query_list.queries), expected, f"Too few queries extracted from {extractor.base_url}"
        )
        self.assertEqual(len(extractor.errors), 0, f"Errors occurred during extraction: {', '.join(extractor.errors)}")

    def _test_extractor(self, extractor, expected: int):
        """
        Helper method to test an extractor by letting it fetch its own content.

        Args:
            extractor: The WikipediaQueryExtractor instance to test.
            expected (int): The minimum number of queries expected to be found.
        """
        if self.debug:
            print(f"extracting queries for {extractor.namespace}@{extractor.domain} ...")

        # Extractor handles fetching internally via Wikidata class if no args provided
        extractor.extract_queries()

        if self.debug:
            extractor.show_queries()
            extractor.show_errors()

        # Basic data validation on extracted queries
        for query in extractor.named_query_list.queries:
            for prop in ["name", "description", "title"]:
                value = getattr(query, prop)
                self.assertNotIn("<translate>", value, f"<translate> tag found in {prop} for {query.query_id}")

        # Test storage persistence
        extractor.store_queries()
        json_filename = f"wikidata-{extractor.namespace}.json"
        extractor.save_to_json(f"/tmp/{json_filename}")

        self.assertGreaterEqual(
            len(extractor.named_query_list.queries), expected, f"No queries extracted from {extractor.base_url}"
        )
        self.assertEqual(len(extractor.errors), 0, f"Errors occurred during extraction: {', '.join(extractor.errors)}")
