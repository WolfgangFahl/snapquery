"""
Created on 2024-05-03

@author: wf
"""

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

    def testMetaApi(self):
        """
        test the meta api
        """
        for qname, ex_status in [("query_count", 200), ("unknown_query_name", 404)]:
            try:
                meta_data = self.get_json(f"/api/meta_query/{qname}", ex_status)
                if self.debug:
                    print(meta_data)
            except Exception as _ex:
                self.assertEqual(404, ex_status)

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
            path = f"/api/sparql/wikidata.org/snapquery-examples/{example}?limit=10"
            sparql_query = self.getHtml(path)
            if self.debug:
                print(sparql_query)
            self.assertTrue("SELECT" in sparql_query)

    def testQueryApi(self):
        """
        test the RESTFul Query API
        """
        for r_format in ["mediawiki", "github", "latex", "html", "json"]:
            path = f"/api/query/wikidata.org/snapquery-examples/cats.{r_format}?limit=10"
            result = self.getHtml(path)
            if self.debug:
                print(result)

    def testEndpoints(self):
        """
        test different endpoints
        """
        debug = self.debug
        # debug=True
        for endpoint_name in [
            "wikidata",
            # "wikidata-openlinksw",
            "wikidata-qlever"
            # "wikidata-scatter",
        ]:
            path = f"/api/query/wikidata.org/snapquery-examples/cats.json?endpoint_name={endpoint_name}&limit=3"
            result = self.getHtml(path)
            if debug:
                print(result)
