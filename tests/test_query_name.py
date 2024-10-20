"""
Created on 03.07.2024

@author: wf
"""

import tempfile

from ngwidgets.basetest import Basetest

from snapquery.qimport import QueryImport
from snapquery.snapquery_core import NamedQueryManager, QueryName, QueryNameSet


class TestQueryName(Basetest):
    """
    test the QueryName and query name stats class
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_query_name_set(self):
        """
        Test QueryNameSet with various domain and namespace filters, ensuring each meets a minimum expected threshold.
        """
        with tempfile.NamedTemporaryFile() as tmpfile:
            nqm = NamedQueryManager.from_samples(db_path=tmpfile.name)
            qimport = QueryImport(nqm=nqm)
            qimport.import_samples(with_store=True, show_progress=self.debug)
            qns = QueryNameSet(nqm, limit=10)  # Assume a limit is meaningful for the test context
            test_cases = [
                (("", ""), (977, 6, 6, 10)),  # Assume maximum values for names as well
                (
                    ("wikidata.org", "examples"),
                    (302, 1, 1, 5),
                ),  # Specific to 'wikidata.org' and 'examples'
                (
                    ("", "examples"),
                    (309, 3, 1, 7),
                ),  # Any domain with 'examples' namespace
                (
                    ("x-invalid", ""),
                    (0, 0, 0, 0),
                ),  # No results expected for an invalid domain
            ]

            for (domain, namespace), (
                expected_total,
                expected_domains_count,
                expected_namespaces_count,
                expected_names_count,
            ) in test_cases:
                with self.subTest(domain=domain, namespace=namespace):
                    qns.update(domain, namespace)
                    if self.debug:
                        print(qns)
                    self.assertGreaterEqual(
                        qns.total,
                        expected_total,
                        f"Total queries should be at least {expected_total}",
                    )
                    self.assertGreaterEqual(
                        len(qns.domains),
                        expected_domains_count,
                        f"Number of domains should be at least {expected_domains_count}",
                    )
                    self.assertGreaterEqual(
                        len(qns.namespaces),
                        expected_namespaces_count,
                        f"Number of namespaces should be at least {expected_namespaces_count}",
                    )
                    self.assertGreaterEqual(
                        len(qns.names),
                        expected_names_count,
                        f"Number of names should be at least {expected_names_count}",
                    )

    def test_query_name(self):
        """
        test the QueryName class
        """
        test_cases = [
            ("cats", "cats", "examples", "wikidata.org"),
            ("cats--examples", "cats", "examples", "wikidata.org"),
            ("cats--custom", "cats", "custom", "wikidata.org"),
            ("cats--custom@dbpedia.org", "cats", "custom", "dbpedia.org"),
            (
                "complex-query--namespace-with-dash@custom-domain.com",
                "complex-query",
                "namespace-with-dash",
                "custom-domain.com",
            ),
        ]

        for query_id, expected_name, expected_namespace, expected_domain in test_cases:
            with self.subTest(query_id=query_id):
                qn = QueryName.from_query_id(query_id)
                self.assertEqual(qn.name, expected_name)
                self.assertEqual(qn.namespace, expected_namespace)
                self.assertEqual(qn.domain, expected_domain)
                self.assertEqual(
                    qn.query_id,
                    QueryName.get_query_id(qn.name, qn.namespace, qn.domain),
                )

    def test_url_friendly_encoding(self):
        """
        test URL-friendly encoding and decoding
        """
        qn = QueryName(name="query with spaces", namespace="test-namespace", domain="example.com")
        self.assertEqual(qn.query_id, "query-with-spaces--test-namespace@example.com")

        decoded = QueryName.from_query_id(qn.query_id)
        self.assertEqual(decoded.name, "query-with-spaces")
        self.assertEqual(decoded.namespace, "test-namespace")
        self.assertEqual(decoded.domain, "example.com")

    def test_roundtrip(self):
        """
        test roundtrip conversion
        """
        original = QueryName(name="test-query", namespace="test-ns", domain="example.com")
        roundtrip = QueryName.from_query_id(original.query_id)
        self.assertEqual(original.to_dict(), roundtrip.to_dict())

    def test_default_values(self):
        """
        test default values
        """
        qn = QueryName(name="test")
        self.assertEqual(qn.namespace, "examples")
        self.assertEqual(qn.domain, "wikidata.org")
