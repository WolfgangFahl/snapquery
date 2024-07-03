"""
Created on 03.07.2024

@author: wf
"""
from ngwidgets.basetest import Basetest
from snapquery.snapquery_core import QueryName

class TestQueryName(Basetest):
    """
    test the QueryName class
    """
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_query_name(self):
        """
        test the QueryName class
        """
        test_cases = [
            ("cats", "cats", "examples", "wikidata.org"),
            ("cats--examples", "cats", "examples", "wikidata.org"),
            ("cats--custom", "cats", "custom", "wikidata.org"),
            ("cats--custom@dbpedia.org", "cats", "custom", "dbpedia.org"),
            ("complex-query--namespace-with-dash@custom-domain.com", "complex-query", "namespace-with-dash", "custom-domain.com"),
        ]

        for query_id, expected_name, expected_namespace, expected_domain in test_cases:
            with self.subTest(query_id=query_id):
                qn = QueryName.from_query_id(query_id)
                self.assertEqual(qn.name, expected_name)
                self.assertEqual(qn.namespace, expected_namespace)
                self.assertEqual(qn.domain, expected_domain)
                self.assertEqual(qn.query_id, QueryName.get_query_id(qn.name, qn.namespace, qn.domain))

    def test_url_friendly_encoding(self):
        """
        test URL-friendly encoding and decoding
        """
        qn = QueryName(name="query with spaces", namespace="test/namespace", domain="example.com")
        self.assertEqual(qn.query_id, "query%20with%20spaces--test%2Fnamespace@example.com")

        decoded = QueryName.from_query_id(qn.query_id)
        self.assertEqual(decoded.name, "query with spaces")
        self.assertEqual(decoded.namespace, "test/namespace")
        self.assertEqual(decoded.domain, "example.com")

    def test_roundtrip(self):
        """
        test roundtrip conversion
        """
        original = QueryName(name="test query", namespace="test/ns", domain="example.com")
        roundtrip = QueryName.from_query_id(original.query_id)
        self.assertEqual(original.to_dict(), roundtrip.to_dict())

    def test_default_values(self):
        """
        test default values
        """
        qn = QueryName(name="test")
        self.assertEqual(qn.namespace, "examples")
        self.assertEqual(qn.domain, "wikidata.org")
