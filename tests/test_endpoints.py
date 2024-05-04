"""
Created on 2024-05-03

@author: wf
"""

from lodstorage.query import EndpointManager
from ngwidgets.basetest import Basetest


class TestEndpoints(Basetest):
    """
    test endpoint handling according to https://github.com/WolfgangFahl/snapquery/issues/1
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testEndpoints(self):
        """
        test the endpoint handling
        """
        em = EndpointManager()
        ep_names = em.getEndpointNames()
        self.assertTrue("wikidata" in ep_names)
        pass
