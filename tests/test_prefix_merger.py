"""
Created on 2024-05-04

@author: tholzheim
"""

from basemkit.basetest import Basetest
from lodstorage.query import Query

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, QueryPrefixMerger


class TestQueryPrefixMerger(Basetest):
    """
    test TestQueryPrefixMerger
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test__missing_(self):
        """
        test handling of missing prefix merger
        Expected to return default merger in case of missing prefix merger
        """
        default = QueryPrefixMerger.default_merger()
        missing_values = [None, "", "unknown"]
        for value in missing_values:
            with self.subTest(value=value):
                merger = QueryPrefixMerger(value)
                self.assertIn(merger, QueryPrefixMerger)
                self.assertEqual(merger, default)

    def test_default_merger(self):
        """
        test default merger
        """
        self.assertIn(QueryPrefixMerger.default_merger(), QueryPrefixMerger)

    def test_merge_prefixes(self):
        """
        test merge prefixes
        """
        named_query = NamedQuery(name="test", sparql="SELECT * WHERE {?work rdf:label ?label . }")
        query = Query(name=named_query.name, query=named_query.sparql)
        nqm = NamedQueryManager()
        endpoint = nqm.endpoints.get("wikidata")
        with self.subTest(name="test raw merger"):
            raw_prefixed_query = QueryPrefixMerger.merge_prefixes(query, endpoint, QueryPrefixMerger.RAW)
            self.assertEqual(named_query.sparql, raw_prefixed_query)
        with self.subTest(name="test analysis merger"):
            analysis_prefixed_merger = QueryPrefixMerger.merge_prefixes(
                query, endpoint, QueryPrefixMerger.ANALYSIS_MERGER
            )
            expected_query = (
                "PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\nSELECT * WHERE {?work rdf:label ?label . }"
            )
            self.assertEqual(expected_query, analysis_prefixed_merger)

    def test_simple_prefix_merger(self):
        """
        test the simple prefix Merger
        """
        nqm = NamedQueryManager()
        endpoint = nqm.endpoints.get("wikidata")
        sparql_query = "SELECT * WHERE {?work rdf:label ?label . }"
        actual_query = QueryPrefixMerger.simple_prefix_merger(sparql_query, endpoint)
        debug = self.debug
        # debug=True
        if debug:
            print(actual_query)
        self.assertIn("PREFIX rdf:", actual_query)

    def test_analysis_prefix_merger(self):
        """
        test analysis prefix merger
        """
        query = "SELECT * WHERE {?work rdf:label ?label . }"
        expected_query = (
            "PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\nSELECT * WHERE {?work rdf:label ?label . }"
        )
        actual_query = QueryPrefixMerger.analysis_prefix_merger(query)
        self.assertEqual(expected_query, actual_query)

    def test_get_by_name(self):
        """
        get prefix manager by name
        """
        for merger in QueryPrefixMerger:
            self.assertEqual(merger.get_by_name(merger.name), merger)
