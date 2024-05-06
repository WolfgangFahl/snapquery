"""
Created on 2024-05-04

@author: wf
"""
import json
import os
from pathlib import Path

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
        db_path = "/tmp/scholia_queries.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        if self.inPublicCI():
            limit = 10
        else:
            # limit = 10
            limit = None
        nqm = ScholiaQueries.get(db_path, debug=self.debug, limit=limit)
        records = nqm.sql_db.query("select * from NamedQuery where namespace='scholia'")
        json_text = json.dumps(records, indent=2)
        output_file = Path("/tmp/scholia.json")
        output_file.write_text(json_text)

        if self.debug:
            print(json_text)
        # nqm.lookup(name, "scholia")
