import unittest
from pathlib import Path

from lodstorage.query import Query
from lodstorage.sparql import SPARQL
from ngwidgets.basetest import Basetest

from snapquery.query_annotate import (
    QUERY_ITEM_STATS,
    ItemStat,
    SparqlQueryAnnotater,
    Stats,
)
from snapquery.snapquery_core import NamedQuery, NamedQueryManager


class TestSparqlQueryAnnotater(Basetest):
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
        Basetest.inPublicCI(), "Only required to regenerate the query_stats.yaml"
    )
    def test_property_usage(self):
        """
        Tests property_usage over all queries
        """
        nqm = NamedQueryManager.from_samples()
        query = "SELECT * FROM NamedQuery"
        properties = []
        for query_record in nqm.sql_db.queryGen(query):
            named_query = NamedQuery.from_record(record=query_record)
            annotated_query = SparqlQueryAnnotater(
                Query(named_query.query_id, named_query.sparql)
            )
            props = annotated_query.get_used_properties()
            properties.extend(props)
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

