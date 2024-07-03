"""
Created on 2024-05-11

@author: wf
"""
import unittest

from ngwidgets.basetest import Basetest

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, QueryDetails


class TestEndpoints(Basetest):
    """
    test endpoint handling according to https://github.com/WolfgangFahl/snapquery/issues/1
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.nqm = NamedQueryManager()

    def parameterize(self, nq: NamedQuery):
        qd = QueryDetails.from_sparql(query_id=nq.query_id, sparql=nq.sparql)
        # Execute the query
        params_dict = {}
        if qd.params == "q":
            # use Tim Berners-Lee as a example
            params_dict = {"q": "Q80"}
            pass
        return qd, params_dict

    def execute(self, nq: NamedQuery, endpoint_name: str, title: str):
        """
        execute the given named query
        """
        qd, params_dict = self.parameterize(nq)
        if self.debug:
            print(f"{title}: {nq.name} {qd} - via {endpoint_name}")

        _results, stats = self.nqm.execute_query(
            nq,
            params_dict=params_dict,
            endpoint_name=endpoint_name,
        )
        self.nqm.store_stats([stats])
        if self.debug:
            msg = f"{title} executed:"
            if not stats.records:
                msg += f"error {stats.filtered_msg}"
            else:
                msg += f"{stats.records} records found"
            print(msg)

    @unittest.skipIf(Basetest.inPublicCI(), "needs import to run")
    def testQueryExecution(self):
        """
        test the execution of a named query on a certain endpoint
        """
        nq = self.nqm.lookup(name="author_other-locations", domain="scholia.toolforge.org",namespace="named_queries")
        self.execute(nq, endpoint_name="wikidata", title="query")

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
                    self.execute(nq, endpoint_name=endpoint_name, title=f"query {i:3}")
            except Exception as ex:
                ex_id = f"{endpoint_name}::{nq.query_id}"
                errors[ex_id] = ex
        if self.debug:
            for i, error in enumerate(errors, start=1):
                print(f"{i:3}:{str(error)}")
        self.assertEqual(0, len(errors))
