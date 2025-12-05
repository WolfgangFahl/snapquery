"""
Test SIB SPARQL Examples fetching.
Verifies integration between SIB fetcher and Snapquery Core.

Created on 2025-12-02
@author: wf
"""

import os
import unittest

from basemkit.basetest import Basetest

from snapquery.sib_sparql_examples import SibSparqlExamples
from snapquery.snapquery_core import NamedQueryManager


class TestSibExamples(Basetest):
    """
    Test retrieving SIB SPARQL examples using GitHub cache/api.
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    @unittest.skipIf(Basetest.inPublicCI(), "avoid github rate limit in CI")
    def test_sib_examples_fetch_and_store(self):
        """
        Test retrieving SIB examples, populating the DB, and exporting to YAML.
        """
        db_path = "/tmp/sib_examples.db"
        yaml_path = "/tmp/sib_examples.yaml"

        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(yaml_path):
            os.remove(yaml_path)

        nqm = NamedQueryManager.from_samples(db_path=db_path)
        sib_fetcher = SibSparqlExamples(nqm, debug=self.debug)

        # Limit for testing efficiency
        limit = 7  # if self.inPublicCI() else None
        if self.debug:
            print(f"Fetching SIB examples (limit={limit})...")

        loaded_queries = sib_fetcher.extract_queries(limit=limit, debug_print=self.debug)

        self.assertTrue(len(loaded_queries) > 0, "Should have loaded at least one query")
        self.assertEqual(len(sib_fetcher.named_query_set), len(loaded_queries))

        # Verify SQL Database Storage
        records = nqm.sql_db.query(
            """
            SELECT count(*) as count
            FROM NamedQuery
            WHERE namespace=? AND domain=?
            """,
            (sib_fetcher.named_query_set.namespace, sib_fetcher.named_query_set.domain),
        )
        db_count = records[0]["count"]
        self.assertEqual(db_count, len(loaded_queries), "DB count should match loaded count")

        # Verify YAML Export
        if self.debug:
            print(f"Exporting to {yaml_path}...")
        sib_fetcher.save_to_yaml(yaml_path)

        self.assertTrue(os.path.exists(yaml_path))

        # Optional: Read back to verify YamlAble structure
        with open(yaml_path, "r") as f:
            content = f.read()
            self.assertIn("sib-examples", content)
            self.assertIn("queries:", content)

        if self.debug:
            print(f"Successfully processed {db_count} queries.")
