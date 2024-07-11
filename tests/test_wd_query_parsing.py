"""
Created on 2024-05-04
@author: tholzheim
"""
import tempfile
from ngwidgets.basetest import Basetest
from snapquery.snapquery_core import NamedQueryManager
from snapquery.wd_page_query_extractor import WikipediaQueryExtractor


class TestWikipediaQueryParsing(Basetest):
    """
    Test Wikipedia query parsing
    """
    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        with tempfile.NamedTemporaryFile(delete=False) as tmpfile:
            self.nqm = NamedQueryManager.from_samples(db_path=tmpfile.name)
            self.lse_extractor=WikipediaQueryExtractor(
                        nqm=self.nqm,
                        base_url="https://www.wikidata.org/wiki/Wikidata:WikiProject_LSEThesisProject",
                        domain="wikidata.org",
                        namespace="lsethesis",
                        target_graph_name="wikidata",
                        template_name=None
                    )
            self.wikidata_example_extractor=WikipediaQueryExtractor(
                        nqm=self.nqm,
                        base_url="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples",
                        domain="wikidata.org",
                        namespace="examples",
                        target_graph_name="wikidata"
                    )
    
    def test_query_extraction(self):
        """
        Test extraction and parsing of queries from Wikidata example page and WikiProject LSEThesisProject page.
        """    
        # Test Wikidata examples page and LSE example
        wikidata_examples = [
            (self.wikidata_example_extractor,200),
            (self.lse_extractor,15), # actually we expect 19 ...
        ]
        for extractor,expected in wikidata_examples:
            with self.subTest(extractor=extractor):
                self._test_extractor(extractor,expected)
            
    def test_wikidata_thesis_toolkit(self):
        """
        test the Wikidata Thesis Toolkit extraction
        """
        markup="""== Test Query ==\n* LSE doctoral theses 1926-2021 with author links to Wikipedia pages where available https://w.wiki/5aHL"""
        extractor=self.lse_extractor
        extractor.extract_queries(wikitext=markup)
        if self.debug:
            extractor.show_queries()
        
    def _test_extractor(self, extractor, expected:int):
        """
        Helper method to test an extractor
        """
        if self.debug:
            print(f"extracting queries for {extractor.namespace}@{extractor.domain} ...")
        extractor.extract_queries()
        if self.debug:
            extractor.show_queries()
        for query in extractor.named_query_list.queries:
            for prop in ["name","description","title"]:
                value=getattr(query,prop)
                self.assertNotIn('<translate>', value, f"<translate> tag found in {prop} for {query.query_id}")
      
        extractor.store_queries()
        json_filename=f"wikidata-{extractor.namespace}.json"
        extractor.save_to_json(f"/tmp/{json_filename}")

        # Add assertions here to verify the extraction results
        self.assertGreaterEqual(len(extractor.named_query_list.queries), expected, 
                           f"No queries extracted from {extractor.base_url}")
