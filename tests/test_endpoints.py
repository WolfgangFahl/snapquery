"""
Created on 2024-05-03
ActionStats integrated with Grok4 Free suppport on 2025-12-03

@author: wf
"""

import requests
from basemkit.basetest import Basetest
from lodstorage.sparql import SPARQL

from snapquery.snapquery_core import NamedQueryManager
from tests.action_stats import ActionStats


class TestEndpoints(Basetest):
    """
    test endpoint handling according to https://github.com/WolfgangFahl/snapquery/issues/1
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.nqm = NamedQueryManager()
        self.user_agent = "snapquery-test/1.0 (https://github.com/WolfgangFahl/snapquery)"
        self.timeout = 10
        self.minRatio= 0.8

    def testEndpoints(self):
        """
        test the endpoint handling
        """
        ep_names = list(self.nqm.endpoints.keys())
        if self.debug:
            print(ep_names)
        self.assertGreater(len(ep_names), 0)
        self.assertIn("wikidata", ep_names)

    def test_website_availability(self):
        """
        Test website availability for endpoints (HTTP 200).
        """
        stats = ActionStats()
        for ep in self.nqm.endpoints.values():
            try:
                self.assertTrue(hasattr(ep, "website"))
                resp = requests.get(ep.website, headers={"User-Agent": self.user_agent}, timeout=self.timeout)
                is_success = (resp.status_code == 200)
                stats.add(is_success)
                if self.debug:
                    if is_success:
                        print(f"✅ {ep.name} website OK: {ep.website}")
                    else:
                        print(f"❌ {ep.name} website failed: {ep.website} (status: {resp.status_code})")
            except Exception as e:
                stats.add(False)
                if self.debug:
                    print(f"❌ {ep.name} website exception: {str(e)}")
        msg = f"Websites availability {stats} ({stats.ratio:.1%}), need >=60%"
        self.assertGreaterEqual(stats.ratio, self.minRatio, msg)
        if self.debug:
            print(f"SUMMARY websites: {stats}")

    def test_sparql_availability(self):
        """
        Test SPARQL endpoint availability with dummy query: SELECT * WHERE {?s ?p ?o} LIMIT 1.
        """
        dummy_query = "SELECT * WHERE { ?s ?p ?o. } LIMIT 1"
        stats = ActionStats()
        for ep in self.nqm.endpoints.values():
            try:
                sparql = SPARQL.fromEndpointConf(ep)
                lod = sparql.queryAsListOfDicts(dummy_query)
                stats.add(True)
                if self.debug:
                    print(f"✅ {ep.name} SPARQL OK: {len(lod)} rows from {ep.endpoint}")
            except Exception as e:
                stats.add(False)
                if self.debug:
                    print(f"❌ {ep.name} SPARQL failed: {ep.endpoint} ({str(e)})")
        msg = f"SPARQL availability {stats} ({stats.ratio:.1%}), need >=60%"
        self.assertGreaterEqual(stats.ratio, self.minRatio, msg)
        if self.debug:
            print(f"SUMMARY SPARQL: {stats}")