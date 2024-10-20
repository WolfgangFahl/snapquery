import unittest
from collections import Counter
from pathlib import Path

from lodstorage.query import Query
from lodstorage.sparql import SPARQL
from ngwidgets.basetest import Basetest

from snapquery.query_annotate import (
    QUERY_ITEM_STATS,
    FunctionStat,
    ItemStat,
    KeywordStat,
    NamespaceStat,
    SparqlQueryAnnotater,
    Stats,
)
from snapquery.snapquery_core import NamedQuery, NamedQueryManager
from snapquery.sparql_analyzer import SparqlAnalyzer


class TestSparqlQueryAnnotater(Basetest):
    """
    Tests SparqlQueryAnnotater
    """

    def setUp(self, debug=False, profile=True):
        super().setUp(debug=debug, profile=profile)
        self.example_query_raw = """
        PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX wd:  <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
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
        self.query = Query("horse", self.example_query_raw)

    def test_get_used_properties(self):
        """
        Tests get_used_properties
        """
        query = self.query
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

    def test_url_detection(self):
        """
        Tests url_detection
        """
        query_str = """
        PREFIX target: <http://www.wikidata.org/entity/{{ q }}>
        # Egocentric co-author graph for an author
        SELECT ?author1 ?author1Label ?rgb ?author2 ?author2Label
        WHERE {
          ?item wdt:P31 <http://www.wikidata.org/entity/Q5>
        }
        """
        query = Query("test_url", query_str)
        annotated_query = SparqlQueryAnnotater(query)
        props = annotated_query.get_used_properties()
        self.assertEqual(1, len(props))

    @unittest.skipIf(
        Basetest.inPublicCI() or True,
        "Only required to regenerate the query_stats.yaml",
    )
    def test_property_usage(self):
        """
        Tests property_usage over all queries
        """
        nqm = NamedQueryManager.from_samples()
        sparql_analyzer = SparqlAnalyzer()
        query = "SELECT * FROM NamedQuery"
        properties = []
        namespace_iris = []
        keywords = []
        functions = []
        prefixes = []
        for query_record in nqm.sql_db.queryGen(query):
            named_query = NamedQuery.from_record(record=query_record)
            sparql_prefix_fixed = sparql_analyzer.add_missing_prefixes(named_query.sparql)
            annotated_query = SparqlQueryAnnotater(Query(named_query.query_id, sparql_prefix_fixed))
            props = annotated_query.get_used_properties()
            properties.extend(props)
            namespace_iris.extend(annotated_query.get_namespace_iris())
            keywords.extend(annotated_query.get_normalized_keywords())
            functions.extend(annotated_query.get_normalized_functions())
            prefixes.extend(annotated_query.get_used_prefixes())
            print(f"{named_query.query_id}: {len(props)}")
        print(len(properties))
        label_lut = self.get_label_lut(properties)
        stats = Stats("items_used_in_queries")
        for p in properties:
            parts = p.split(":")
            identifier = parts[-1]
            if not identifier.startswith(("P", "Q")):
                identifier = p
            namespace = parts[0]
            label = label_lut.get(identifier)
            if label is None:
                label = p
            item_stat = stats.get_by_id(identifier)
            if item_stat is None:
                item_stat = ItemStat(identifier, label)
                stats.item_stats.append(item_stat)
            item_stat.count += 1
            item_stat.increment_namespace_count(namespace)
        # add keyword stats
        for keyword, count in Counter(keywords).items():
            stats.keyword_stats.append(KeywordStat(keyword, count))
        # add function stats
        for name, count in Counter(functions).items():
            stats.function_stats.append(FunctionStat(name, count))
        # add namespace stats
        for prefix, count in Counter(prefixes).items():
            iri = sparql_analyzer.get_prefix_iri(prefix)
            if isinstance(count, int):
                count -= 1
            stats.namespace_stats.append(NamespaceStat(prefix, iri, count))
        target_path = Path("/tmp/query_stats.yaml")
        stats.save_to_yaml_file(target_path)

    def get_label_lut(self, properties: list[str]) -> dict[str, str]:
        query_label = """
                SELECT DISTINCT *
                WHERE{
                  VALUES ?item {%s}
                  ?item rdfs:label ?itemLabel. FILTER(lang(?itemLabel)="en")
                }
                """
        prop_set = {f"wd:{p.split(':')[-1]}" for p in properties}
        sparql = SPARQL("https://query.wikidata.org/sparql", method="POST")
        lod = sparql.queryAsListOfDicts(query_label % "\n".join(prop_set))
        label_lut = {}
        for d in lod:
            identifier = d.get("item")[len("http://www.wikidata.org/entity/") :]
            label = d.get("itemLabel")
            if identifier in label_lut:
                print(f"duplicate {identifier}: {label_lut[identifier]} vs. {label}")
            label_lut[identifier] = label
        return label_lut

    def test_plot_property_usage(self):
        """
        Tests plot_property_usage over all queries
        """
        stats = QUERY_ITEM_STATS

    def test_keyword_extraction(self):
        """
        test extracting keywords from a sparql query
        """
        query = self.query
        annotated_query = SparqlQueryAnnotater(query)
        used_keywords = annotated_query.get_used_keywords()
        expected_keywords = [
            "PREFIX",
            "PREFIX",
            "PREFIX",
            "SELECT",
            "DISTINCT",
            "as",
            "as",
            "WHERE",
            "OPTIONAL",
            "OPTIONAL",
            "OPTIONAL",
            "OPTIONAL",
            "OPTIONAL",
            "OPTIONAL",
            "FILTER",
            "OPTIONAL",
            "FILTER",
            "OPTIONAL",
            "FILTER",
            "OPTIONAL",
            "FILTER",
            "ORDER BY",
        ]
        self.assertEqual(used_keywords, expected_keywords)

    def test_namespace_iri_extraction(self):
        """
        test extracting keywords from a sparql query
        """
        query = self.query
        annotated_query = SparqlQueryAnnotater(query)
        used_namespace_iris = annotated_query.get_namespace_iris()
        expected_namespace_iris = [
            "http://www.w3.org/2000/01/rdf-schema#",
            "http://www.wikidata.org/entity/",
            "http://www.wikidata.org/prop/direct/",
        ]
        self.assertEqual(used_namespace_iris, expected_namespace_iris)

    def test_function_extraction(self):
        """
        test extraction of SPARQL functions
        """
        query = self.query
        annotated_query = SparqlQueryAnnotater(query)
        used_namespace_iris = annotated_query.get_used_functions()
        expected_namespace_iris = ["year", "year", "lang", "lang", "lang", "lang"]
        self.assertEqual(used_namespace_iris, expected_namespace_iris)
