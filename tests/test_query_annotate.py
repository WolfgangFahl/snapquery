import unittest
from lodstorage.query import Query
from snapquery.query_annotate import SparqlQueryAnnotater


class TestSparqlQueryAnnotater(unittest.TestCase):
    """
    Tests SparqlQueryAnnotater
    """
    def test_get_used_properties(self):
        """
        Tests get_used_properties
        """
        query_str = """
        SELECT DISTINCT ?horse ?horseLabel ?mother ?motherLabel ?father ?fatherLabel 
        (year(?birthdate) as ?birthyear) (year(?deathdate) as ?deathyear) ?genderLabel
        WHERE {
          ?horse wdt:P31/wdt:P279* wd:Q726 .     # Instance and subclasses of horse (Q726)
          OPTIONAL{?horse wdt:P25 ?mother .}     # Mother
          OPTIONAL{?horse wdt:P22 ?father .}     # Father
          OPTIONAL{?horse wdt:P569 ?birthdate .} # Birth date
          OPTIONAL{?horse wdt:P570 ?deathdate .} # Death date
          OPTIONAL{?horse wdt:P21 ?gender .}     # Gender
          OPTIONAL { ?horse rdfs:label ?horseLabel . FILTER (lang(?horseLabel) = "en") }
          OPTIONAL { ?mother rdfs:label ?motherLabel . FILTER (lang(?motherLabel) = "en") }
          OPTIONAL { ?father rdfs:label ?fatherLabel . FILTER (lang(?fatherLabel) = "en") }
          OPTIONAL { ?gender rdfs:label ?genderLabel . FILTER (lang(?genderLabel) = "en") }
        }
        ORDER BY ?horse
        """
        query = Query("horse", query_str)
        annotated_query = SparqlQueryAnnotater(query)
        props = annotated_query.get_used_properties()
        self.assertEqual(len(props), 12)
        expected_items = [
            "wdt:P31",
            "wdt:P279",
            "wd:Q726",
            "wdt:P25",
            "wdt:P22",
            "wdt:P569",
            "wdt:P570",
            "wdt:P21",
            "rdfs:label",
            "rdfs:label",
            "rdfs:label",
            "rdfs:label",
        ]
        self.assertListEqual(expected_items, props)


if __name__ == "__main__":
    unittest.main()
