"""
Created on 2024-05-03

@author: wf
"""
import json

from ngwidgets.webserver_test import WebserverTest

from snapquery.snapquery_cmd import SnapQueryCmd
from snapquery.snapquery_webserver import SnapQueryWebServer


class TestRestFulApi(WebserverTest):
    """
    test endpoint handling according to https://github.com/WolfgangFahl/snapquery/issues/1
    """

    def setUp(self, debug=False, profile=True):
        server_class = SnapQueryWebServer
        cmd_class = SnapQueryCmd
        WebserverTest.setUp(self, server_class, cmd_class, debug=debug, profile=profile)

    def testDemoWebserver(self):
        """
        test API docs access
        """
        # self.debug=True
        html = self.getHtml("/docs")
        self.assertTrue("Swagger" in html)

    def testEndpointApi(self):
        """
        test the endpoints api
        """
        endpoints_data = self.get_json("/api/endpoints")
        if self.debug:
            print(endpoints_data)
        self.assertTrue("wikidata" in endpoints_data)

    def testSparqlApi(self):
        """
        test the plaintext SPARQL API
        """
        for example in ["cats", "horses"]:
            path = f"/api/sparql/wikidata-examples/{example}?limit=10"
            sparql_query = self.getHtml(path)
            if self.debug:
                print(sparql_query)
            self.assertTrue("SELECT" in sparql_query)

    def testQueryApi(self):
        """
        test the RESTFul Query API
        """
        for r_format in ["mediawiki", "github", "latex", "html", "json"]:
            path = f"/api/query/wikidata-examples/cats.{r_format}?limit=10"
            result = self.getHtml(path)
            if self.debug:
                print(result)
