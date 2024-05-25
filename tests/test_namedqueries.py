"""
Created on 2024-05-03

@author: wf
"""

import json
import tempfile

from ngwidgets.basetest import Basetest

from snapquery.snapquery_core import NamedQuery, NamedQueryManager


class TestNamedQueryManager(Basetest):
    """
    test the named query Manager
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_named_queries(self):
        """
        test getting a named query manager
        """
        with tempfile.NamedTemporaryFile() as tmpfile:
            nqm = NamedQueryManager.from_samples(db_path=tmpfile.name)
            for name, ex_count in [("x-invalid", -1), ("cats", 207)]:
                try:
                    query_bundle = nqm.get_query(
                        namespace="snapquery-examples", name=name
                    )
                    lod = query_bundle.get_lod()
                    if self.debug:
                        print(f"{name}:")
                        print(json.dumps(lod, default=str, indent=2))
                    self.assertTrue(len(lod) >= ex_count)
                except Exception as ex:
                    if self.debug:
                        print(f"{name}:Exception {str(ex)}")
                        self.assertEqual(-1, ex_count)

    def test_query_with_stats(self):
        """
        tests executing a query with stats
        """
        with tempfile.NamedTemporaryFile() as tmpfile:
            nqm = NamedQueryManager.from_samples(db_path=tmpfile.name)
            query_bundle = nqm.get_query(namespace="snapquery-examples", name="cats")
            lod, query_stats = query_bundle.get_lod_with_stats()
            self.assertEqual(query_bundle.named_query.query_id, query_stats.query_id)
            self.assertEqual(query_stats.endpoint_name, query_bundle.endpoint.name)
            self.assertEqual(len(lod), query_stats.records)
            self.assertIsNone(query_stats.error_msg)
            self.assertIsNotNone(query_stats.duration)

    def test_meta_queries(self):
        """
        test meta queries
        """
        nqm = NamedQueryManager.from_samples()
        self.assertTrue("query_count" in nqm.meta_qm.queriesByName)
        pass

    def test_query_with_stats_evaluation(self):
        """
        test query stats evaluation and storage on a bunch of queries
        """
        nqm = NamedQueryManager.from_samples(db_path="/tmp/stats_eval.db")
        limit = 1
        if self.inPublicCI():
            limit = 2
        query_records = nqm.sql_db.query(
            f"SELECT * FROM NamedQuery WHERE namespace='snapquery-examples' LIMIT {limit}"
        )
        query_stats_list = []
        for i, query_record in enumerate(query_records):
            named_query = NamedQuery.from_record(query_record)
            query_bundle = nqm.get_query(
                named_query.name,
                named_query.namespace,
                endpoint_name="wikidata-openlinksw",
            )
            if self.debug:
                print(f"{i+1:3}/{len(query_records)}:{named_query.query_id}")
            lod, query_stats = query_bundle.get_lod_with_stats()
            lod_len = len(lod) if lod else 0
            if self.debug:
                print(f"    {lod_len} records:{query_stats.duration:.1f} s")
            query_stats_list.append(query_stats)
        nqm.store_stats(query_stats_list)
