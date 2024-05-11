"""
Created on 2024-05-03

@author: wf
"""

from snapquery.snapquery_core import NamedQueryManager
from ngwidgets.basetest import Basetest


class TestEndpoints(Basetest):
    """
    test endpoint handling according to https://github.com/WolfgangFahl/snapquery/issues/1
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.nqm=NamedQueryManager()

    def testEndpoints(self):
        """
        test the endpoint handling
        """
        ep_names = self.nqm.endpoints.keys()
        if self.debug:
            print(ep_names)
        self.assertTrue("wikidata" in ep_names)
        pass
    
   
        
