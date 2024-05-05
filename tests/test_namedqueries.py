"""
Created on 2024-05-03

@author: wf
"""

import json
import tempfile
import unittest

from ngwidgets.basetest import Basetest

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, QueryStats


class TestNamedQueryManager(Basetest):
    """
    test the named query Manager
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testNamedQueries(self):
        """
        test getting a named query manager
        """
        db_path = "/tmp/named_queries.db"
        nqm = NamedQueryManager.from_samples(db_path=db_path)
        for name, ex_count in [("x-invalid", -1), ("cats", 223)]:
            try:
                query_bundle = nqm.get_query(name)
                lod = query_bundle.get_lod()
                if self.debug:
                    print(f"{name}:")
                    print(json.dumps(lod, default=str, indent=2))
                self.assertEqual(ex_count, len(lod))
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
            query_bundle = nqm.get_query("cats")
            lod, query_stats = query_bundle.get_lod_with_stats()
            self.assertEqual(query_bundle.query.name, query_stats.query_id)
            self.assertEqual(query_stats.endpoint_name, query_bundle.endpoint.name)
            self.assertIsNone(query_stats.error_msg)
            self.assertIsNotNone(query_stats.duration)

    @unittest.skip
    def test_query_with_stats_evaluation(self):
        """
        test query stats evaluation and storage on a bunch of queries
        """
        nqm = NamedQueryManager.from_samples()
        query_records = nqm.sql_db.query("SELECT * FROM NamedQuery LIMIT 20")
        query_stats = []
        for query_record in query_records:
            named_query = NamedQuery.from_record(query_record)
            query_bundle = nqm.get_query(named_query.name, named_query.namespace)
            lod, query_stat = query_bundle.get_lod_with_stats()
            query_stats.append(query_stat)
        stat_lod = [qs.as_record() for qs in query_stats]
        nqm.store(stat_lod, source_class=QueryStats, primary_key="stats_id")