"""
Created on 2024-05-04

@author: wf
"""

import os

from ngwidgets.basetest import Basetest

from snapquery.scholia import ScholiaQueries
from snapquery.snapquery_core import NamedQueryManager


class TestScholia(Basetest):
    """
    test scholia queries
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_scholia_queries(self):
        """
        Test retrieving Scholia queries.
        """
        db_path = "/tmp/scholia_queries.db"
        if os.path.exists(db_path):
            os.remove(db_path)

        # Adjust limit based on environment (e.g., CI)
        if self.inPublicCI():
            limit = 10
        else:
            limit = None
            #limit=10

        # Create a NamedQueryManager and ScholiaQueries instance
        nqm = NamedQueryManager.from_samples(db_path=db_path)
        scholia_queries = ScholiaQueries(nqm, debug=self.debug)

        # Extract, store, and save queries to JSON
        scholia_queries.extract_queries(limit=limit)
        scholia_queries.store_queries()
        scholia_queries.save_to_json("/tmp/scholia.json")

        # Verify the data was stored
        records = nqm.sql_db.query(f"""SELECT * 
FROM NamedQuery 
WHERE namespace='{scholia_queries.named_query_set.namespace}'
AND domain='{scholia_queries.named_query_set.domain}'
""")
        self.assertEqual(len(records), len(scholia_queries.named_query_set.queries))
