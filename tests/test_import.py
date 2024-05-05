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
        query = url_import.import_from_url(url, debug=self.debug)
        if self.debug:
            print(query)
