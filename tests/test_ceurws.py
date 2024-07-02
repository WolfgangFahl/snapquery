"""
Created on 2024-07-02
@autor: wf
@author: Claude (AI Assistant)
"""
import os
import unittest

from ngwidgets.basetest import Basetest

from snapquery.ceurws import CeurWSQueries
from snapquery.snapquery_core import NamedQueryManager


class TestCeurWS(Basetest):
    """
    test CEUR-WS queries
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    @unittest.skipIf(Basetest.inPublicCI(), "credentials need for execution in CI")
    def test_ceurws_queries(self):
        """
        Test retrieving CEUR-WS queries.
        """
        db_path = "/tmp/ceur-ws_queries.db"
        if os.path.exists(db_path):
            os.remove(db_path)

        # Adjust limit based on environment (e.g., CI)
        if self.inPublicCI():
            limit = 10
        else:
            limit = None

        # Create a NamedQueryManager and CeurWSQueries instance
        nqm = NamedQueryManager.from_samples(db_path=db_path)
        ceurws_queries = CeurWSQueries(nqm, debug=self.debug)

        # Extract, store, and save queries to JSON
        ceurws_queries.extract_queries(limit=limit)
        ceurws_queries.store_queries()
        ceurws_queries.save_to_json("/tmp/ceur-ws.json")

        # Verify the data was stored
        records = nqm.sql_db.query(
            f"""SELECT * 
        FROM NamedQuery 
        WHERE namespace='{ceurws_queries.named_query_set.namespace}'
        AND domain='{ceurws_queries.named_query_set.domain}'
        """
        )
        self.assertEqual(len(records), len(ceurws_queries.named_query_set.queries))

