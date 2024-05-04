"""
Created on 2024-05-03

@author: wf
"""

import json

from ngwidgets.basetest import Basetest

from snapquery.snapquery_core import NamedQueryManager


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
