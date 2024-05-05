"""
Created on 2024-05-04

@author: wf
"""
from pathlib import Path
from ngwidgets.basetest import Basetest

from snapquery.scholia import ScholiaQueries
import json

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
        limit = 10
        if self.inPublicCI():
            db_path = "/tmp/scholia_queries.db"
        else:
            db_path = None
            #limit = None
        nqm = ScholiaQueries.get(db_path, debug=self.debug, limit=limit)
        records=nqm.sql_db.query("select * from NamedQuery")
        json_text=json.dumps(records,indent=2)
        output_file = Path("/tmp/scholia.json")
        output_file.write_text(json_text)

        if self.debug:
            print(json_text)
        #nqm.lookup(name, "scholia")