"""
Created on 2024-05-05

@author: wf
"""
from ngwidgets.basetest import Basetest

from snapquery.snapquery_core import NamedQueryManager
from snapquery.urlimport import UrlImport


class TestImport(Basetest):
    """
    test importing  named queries
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testImport(self):
        """
        test importing named queries
        """
        url = "https://w.wiki/6UCU"
        url_import = UrlImport()
        query = url_import.read_from_short_url(url)
        if self.debug:
            print(query)
        self.assertTrue("Q0.1" in query)
