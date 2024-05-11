"""
Created on 2024-05-11

@author: wf
"""
from snapquery.snapquery_core import NamedQueryManager
from ngwidgets.basetest import Basetest
import random

class TestEndpoints(Basetest):
    """
    test endpoint handling according to https://github.com/WolfgangFahl/snapquery/issues/1
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.nqm=NamedQueryManager()

    def testQueryExecution(self):
        """
        Test executing queries from the NamedQueryManager by using the as_query_bundle method to 
        assemble and prepare each query with a specific endpoint and limit for execution.
        """
        endpoint_names=list(self.nqm.endpoints.keys())
        if self.inPublicCI():
            limit=5
        else:    
            limit = 50
        queries = self.nqm.get_all_queries()
        errors={}
        for i, named_query in enumerate(queries, start=1):
            if i > limit:
                break
            try:
                for endpoint_name in endpoint_names:  # Specify the default endpoint to test against
                    if self.debug:
                        print(f"{i:4}: {named_query.name} - via {endpoint_name}")
                    # Execute the query (actual execution method depends on your QueryBundle implementation)
                    _results, stats = self.nqm.execute_query(named_query, endpoint_name)
                    self.nqm.store_stats([stats])
                    print(f"Query {i} executed: {stats.records} records found")
            except Exception as ex:
                ex_id=f"{named_query.query_id}::{endpoint_name}"
                errors[ex_id]=ex
        if self.debug:
            for i,error in enumerate(errors,start=1):
                print(f"{i:3}:{str(error)}")
        self.assertEqual(0,len(errors))