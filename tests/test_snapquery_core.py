from unittest import TestCase

from lodstorage.query import Query

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, QueryPrefixMerger



class TestQueryPrefixMerger(TestCase):
    """
    test TestQueryPrefixMerger
    """

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
            raw_prefixed_query = QueryPrefixMerger.merge_prefixes(named_query, query, endpoint, QueryPrefixMerger.RAW)
            self.assertEqual(named_query.sparql, raw_prefixed_query)
        with self.subTest(name="test simple prefix merger"):
            simple_prefixed_query = QueryPrefixMerger.merge_prefixes(
                named_query, query, endpoint, QueryPrefixMerger.SIMPLE_MERGER
            )
            expected_simple_query = f"{endpoint.prefixes}\nSELECT * WHERE {{?work rdf:label ?label . }}"
            self.assertEqual(expected_simple_query, simple_prefixed_query)
        with self.subTest(name="test analysis merger"):
            analysis_prefixed_merger = QueryPrefixMerger.merge_prefixes(
                named_query, query, endpoint, QueryPrefixMerger.ANALYSIS_MERGER
            )
            expected_query = (
                "PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\nSELECT * WHERE {?work rdf:label ?label . }"
            )
            self.assertEqual(expected_query, analysis_prefixed_merger)

    def test_simple_prefix_merger(self):
        nqm = NamedQueryManager()
        endpoint = nqm.endpoints.get("wikidata")
        query = "SELECT * WHERE {?work rdf:label ?label . }"
        expected_query = f"{endpoint.prefixes}\nSELECT * WHERE {{?work rdf:label ?label . }}"
        actual_query = QueryPrefixMerger.simple_prefix_merger(query, endpoint)
        self.assertEqual(expected_query, actual_query)

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
        for merger in QueryPrefixMerger:
            self.assertEqual(merger.get_by_name(merger.name), merger)
