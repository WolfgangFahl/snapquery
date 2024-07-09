"""
Created on 2024-05-11

@author: wf
"""
import unittest

from ngwidgets.basetest import Basetest

from snapquery.snapquery_core import  QueryName,NamedQueryManager
from snapquery.execution import Execution

class TestEndpoints(Basetest):
    """
    test endpoint handling according to https://github.com/WolfgangFahl/snapquery/issues/1
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.nqm = NamedQueryManager()
        self.execution=Execution(self.nqm)
    

    @unittest.skipIf(Basetest.inPublicCI(), "needs import to run")
    def testQueryExecution(self):
        """
        test the execution of a named query on a certain endpoint
        """
        q_name=QueryName(name="author_other-locations",
            domain="scholia.toolforge.org",
            namespace="named_queries")
        nq = self.nqm.lookup(q_name)
        self.execution.execute(nq, endpoint_name="wikidata", title="query")

    @unittest.skipIf(Basetest.inPublicCI(), "needs import to run")
    def testQueryExecutions(self):
        """
        Test executing queries from the NamedQueryManager by using the as_query_bundle method to
        assemble and prepare each query with a specific endpoint and limit for execution.
        """
        endpoint_names = list(self.nqm.endpoints.keys())
        if self.inPublicCI():
            limit = 5
        else:
            limit = 50
        queries = self.nqm.get_all_queries()
        errors = {}
        for i, nq in enumerate(queries, start=1):

            if i > limit:
                break
            try:
                for (
                    endpoint_name
                ) in endpoint_names:  # Specify the default endpoint to test against
                    self.execution.execute(nq, endpoint_name=endpoint_name, title=f"query {i:3}")
            except Exception as ex:
                ex_id = f"{endpoint_name}::{nq.query_id}"
                errors[ex_id] = ex
        if self.debug:
            for i, error in enumerate(errors, start=1):
                print(f"{i:3}:{str(error)}")
        self.assertEqual(0, len(errors))
