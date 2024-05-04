"""
Created on 2024-05-04

@author: wf
"""
from ngwidgets.basetest import Basetest

from snapquery.scholia import ScholiaQueries


class TestScholia(Basetest):
    """
    test scholia queries
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_scholia_queries(self):
        """
        test retrieving scholia queries
        """
        if self.inPublicCI():
            db_path = "/tmp/scholia_queries.db"
            limit = 10
        else:
            db_path = None
            limit = None
        nqm = ScholiaQueries.get(db_path, debug=self.debug, limit=limit)
