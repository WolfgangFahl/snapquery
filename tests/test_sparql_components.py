import unittest

from basemkit.basetest import Basetest

from snapquery.models.sparql_components import SPARQLLanguage


class TestSPARQLLanguage(Basetest):
    """
    test SPARQLLanguage class
    """

    def test_get_keyword_wd_entity(self):
        sparql_language = SPARQLLanguage.load_sparql_language()
        select_entity = sparql_language.get_keyword_wd_entity("SELECT")
        self.assertEqual(str(select_entity), "http://www.wikidata.org/entity/Q130564533")

    def test_get_function_wd_entity(self):
        sparql_language = SPARQLLanguage.load_sparql_language()
        select_entity = sparql_language.get_function_wd_entity("STR")
        self.assertEqual(str(select_entity), "http://www.wikidata.org/entity/Q130564604")

    @unittest.skip("Only needed to update the sparql language model")
    def test_reload_data_from_wikidata(self):
        sparql_language = SPARQLLanguage.load_sparql_language_data_from_wikidata()
        self.assertIsInstance(sparql_language, SPARQLLanguage)
        language = SPARQLLanguage.load_sparql_language()
        self.assertIsInstance(language, SPARQLLanguage)
        self.assertGreaterEqual(len(language.keywords), 10)
        self.assertGreaterEqual(len(language.functions), 10)
