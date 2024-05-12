"""
Created on 2024-05-04

@author: tholzheim
"""
import pprint
import tempfile

from ngwidgets.basetest import Basetest

from snapquery.snapquery_core import NamedQueryManager
from snapquery.wd_examples import WikidataExamples


class TestWdQueryParsing(Basetest):
    """
    test wikidata query parsing
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_wikidata_examples_query_extraction(self):
        """
        Test extraction and parsing of Wikidata example queries to NamedQueries.

        Queries can be found at https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples
        """
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            nqm = NamedQueryManager.from_samples(db_path=tmpfile.name)
            self.wikidata_examples = WikidataExamples(nqm)
            self.wikidata_examples.extract_queries()
            if self.debug:
                for query in self.wikidata_examples.named_query_list.queries:
                    pprint.pprint(query)

        if self.debug:
            print(
                f"found {len(self.wikidata_examples.named_query_list.queries)} queries"
            )

        self.wikidata_examples.store_queries()
        self.wikidata_examples.save_to_json("/tmp/wikidata-examples.json")
