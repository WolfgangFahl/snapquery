"""
Created on 2024-05-03

@author: wf
"""

from ngwidgets.basetest import Basetest
from snapquery.snapquery_core import NamedQueryManager
import requests
from lodstorage.sparql import SPARQL

class TestEndpoints(Basetest):
    """
    test endpoint handling according to https://github.com/WolfgangFahl/snapquery/issues/1
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.nqm = NamedQueryManager()
        self.user_agent = 'snapquery-test/1.0 (https://github.com/WolfgangFahl/snapquery)'
        self.timeout = 10

    def testEndpoints(self):
        """
        test the endpoint handling
        """
        ep_names = self.nqm.endpoints.keys()
        if self.debug:
            print(ep_names)
        self.assertTrue("wikidata" in ep_names)
        pass


    def test_website_availability(self):
        """
        Test website availability forendpoints (HTTP 200).
        """
        for ep in self.nqm.endpoints.values():
            self.assertTrue(hasattr(ep, 'website'))
            resp = requests.get(
                ep.website,
                headers={'User-Agent': self.user_agent},
                timeout=self.timeout
            )
            self.assertEqual(
                resp.status_code, 200,
                f"Website {ep.website} for {ep.name} unavailable (status: {resp.status_code})"
            )
            if self.debug:
                print(f"✅ {ep.name} website OK: {ep.website}")

    def test_sparql_availability(self):
        """
        Test SPARQL endpoint availability with dummy query: SELECT * WHERE {?s ?p ?o} LIMIT 1.
        """
        dummy_query = "SELECT * WHERE { ?s ?p ?o. } LIMIT 1"
        for ep in self.nqm.endpoints.values():
            try:
                sparql = SPARQL.fromEndpointConf(ep)
                lod = sparql.queryAsListOfDicts(dummy_query)
                self.assertGreaterEqual(
                    len(lod), 0,
                    f"SPARQL {ep.endpoint} for {ep.name} returned no results"
                    )
                if self.debug:
                    print(f"✅ {ep.name} SPARQL OK: {len(lod)} rows from {ep.endpoint}")
            except Exception as e:
                self.fail(f"SPARQL check failed for {ep.name}: {str(e)}")