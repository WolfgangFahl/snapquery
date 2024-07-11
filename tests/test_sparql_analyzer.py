import logging
import pprint
import sys
import unittest

import snapquery.sparql_analyzer
from snapquery.snapquery_core import NamedQueryManager
from snapquery.sparql_analyzer import SparqlAnalyzer

logging.basicConfig(level=logging.DEBUG)
logger = logging.root
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
logger.setLevel(logging.DEBUG)


class TestSparqlAnalyzer(unittest.TestCase):
    """
    Tests the Sparql Analyzer class.
    """

    def test_is_valid(self):
        test_params = [
            ("""SELECT DISTINCT * WHERE { ?astronaut wdt:P106 wd:Q11631 .}""", False),
            (
                """PREFIX wd: <http://www.wikidata.org/entity/>\nPREFIX wdt: <http://www.wikidata.org/prop/direct/>\n SELECT DISTINCT * WHERE { ?astronaut wdt:P106 wd:Q11631 .}""",
                True,
            ),
        ]
        for query, expected_res in test_params:
            actual = SparqlAnalyzer.is_valid(query)
            self.assertEqual(expected_res, actual)

    @unittest.skip("Skip until the named query refactoring is finished")
    def test_all_sample_queries(self):
        """
        test all sample queries.
        """
        nqm = NamedQueryManager()
        namespaces = [
            "challenge",
            # "named_queries"  # all queries works except one which expects a datetime parameter which is not detected
        ]
        for namespace in namespaces:
            queries = nqm.get_all_queries(namespace)
            for query in queries:
                with self.subTest(query=query):
                    try:
                        fixed_query = SparqlAnalyzer.add_missing_prefixes(query.sparql)
                        if SparqlAnalyzer.has_parameter(fixed_query):
                            fixed_query = SparqlAnalyzer.fill_with_sample_query_parameters(fixed_query)
                        if SparqlAnalyzer.has_blazegraph_with_clause(fixed_query):
                            fixed_query = SparqlAnalyzer.transform_with_clause_to_subquery(fixed_query)
                        is_valid = SparqlAnalyzer.is_valid(fixed_query)
                        if not is_valid:
                            print(query.query_id)
                        # self.assertTrue(is_valid)
                    except Exception as e:
                        print(query.query_id)
                        raise e

    def test_extract_used_prefixes(self):
        """
        test extract used prefixes.
        """
        sparql = """
PREFIX imdb: <https://www.imdb.com/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?movie ?imdb_id ?title (MIN(YEAR(?date)) AS ?year) ?imdb_votes ?imdb_rating WHERE {
  ?movie wdt:P31 wd:Q11424 .
  ?movie wdt:P345 ?imdb_id .
  ?movie wdt:P577 ?date .
  ?movie rdfs:label ?title FILTER (LANG(?title) = "en") .
  SERVICE <https://qlever.cs.uni-freiburg.de/api/imdb> {
    ?movie_imdb imdb:id ?imdb_id .
    ?movie_imdb imdb:type "movie" .
    ?movie_imdb imdb:numVotes ?imdb_votes .
    ?movie_imdb imdb:averageRating ?imdb_rating .
  }
}
GROUP BY ?movie ?title ?imdb_id ?imdb_votes ?imdb_rating
ORDER BY DESC(?imdb_votes)
        """
        declared_prefixes, used_prefixes = SparqlAnalyzer.extract_used_prefixes(sparql)
        self.assertSetEqual({"rdfs", "imdb"}, set(declared_prefixes.keys()))
        self.assertSetEqual({"wdt", "wd", "rdfs", "imdb"}, used_prefixes)

    def test_add_missing_prefixes(self):
        """
        test add_missing_prefixes
        """
        sparql = """PREFIX imdb: <https://www.imdb.com/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?movie ?imdb_id ?title (MIN(YEAR(?date)) AS ?year) ?imdb_votes ?imdb_rating WHERE {
  ?movie wdt:P31 wd:Q11424 .
  ?movie wdt:P345 ?imdb_id .
  ?movie wdt:P577 ?date .
  ?movie rdfs:label ?title FILTER (LANG(?title) = "en") .
  SERVICE <https://qlever.cs.uni-freiburg.de/api/imdb> {
    ?movie_imdb imdb:id ?imdb_id .
    ?movie_imdb imdb:type "movie" .
    ?movie_imdb imdb:numVotes ?imdb_votes .
    ?movie_imdb imdb:averageRating ?imdb_rating .
  }
}
GROUP BY ?movie ?title ?imdb_id ?imdb_votes ?imdb_rating
ORDER BY DESC(?imdb_votes)
        """
        expected_sparql = """PREFIX wd:  <http://www.wikidata.org/entity/>
PREFIX wdt:  <http://www.wikidata.org/prop/direct/>
PREFIX imdb: <https://www.imdb.com/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT ?movie ?imdb_id ?title (MIN(YEAR(?date)) AS ?year) ?imdb_votes ?imdb_rating WHERE {
  ?movie wdt:P31 wd:Q11424 .
  ?movie wdt:P345 ?imdb_id .
  ?movie wdt:P577 ?date .
  ?movie rdfs:label ?title FILTER (LANG(?title) = "en") .
  SERVICE <https://qlever.cs.uni-freiburg.de/api/imdb> {
    ?movie_imdb imdb:id ?imdb_id .
    ?movie_imdb imdb:type "movie" .
    ?movie_imdb imdb:numVotes ?imdb_votes .
    ?movie_imdb imdb:averageRating ?imdb_rating .
  }
}
GROUP BY ?movie ?title ?imdb_id ?imdb_votes ?imdb_rating
ORDER BY DESC(?imdb_votes)
        """
        fixed_query = SparqlAnalyzer.add_missing_prefixes(sparql)
        self.assertEqual(expected_sparql, fixed_query)

    def test_transform_with_clause_to_subquery(self):
        """
        test transform_with_clause_to_subquery
        """
        query = """
SELECT ?mol ?molLabel ?InChIKey ?CAS ?ChemSpider ?PubChem_CID WITH {
  SELECT ?mol ?InChIKey WHERE {
    SERVICE wikibase:mwapi {
        bd:serviceParam wikibase:endpoint "www.wikidata.org";
        wikibase:api "Search";
        mwapi:srsearch "_shortkey_ haswbstatement:P235";
        mwapi:srlimit "max".
        ?mol wikibase:apiOutputItem mwapi:title.
      }
    ?mol wdt:P235 ?InChIKey .
    FILTER (regex(str(?InChIKey), "^_shortkey_"))
  }
} AS %MOLS {
  INCLUDE %MOLS
  OPTIONAL { ?mol wdt:P231 ?CAS }
  OPTIONAL { ?mol wdt:P661 ?ChemSpider }
  OPTIONAL { ?mol wdt:P662 ?PubChem_CID }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
        """
        expected_query = """
SELECT ?mol ?molLabel ?InChIKey ?CAS ?ChemSpider ?PubChem_CID 
WHERE
{
  {  SELECT ?mol ?InChIKey WHERE {
    SERVICE wikibase:mwapi {
        bd:serviceParam wikibase:endpoint "www.wikidata.org";
        wikibase:api "Search";
        mwapi:srsearch "_shortkey_ haswbstatement:P235";
        mwapi:srlimit "max".
        ?mol wikibase:apiOutputItem mwapi:title.
      }
    ?mol wdt:P235 ?InChIKey .
    FILTER (regex(str(?InChIKey), "^_shortkey_"))
  }
}

  OPTIONAL { ?mol wdt:P231 ?CAS }
  OPTIONAL { ?mol wdt:P661 ?ChemSpider }
  OPTIONAL { ?mol wdt:P662 ?PubChem_CID }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
        """

        self.assertTrue(SparqlAnalyzer.has_blazegraph_with_clause(query))
        self.assertFalse(SparqlAnalyzer.has_blazegraph_with_clause(expected_query))
        fixed_query = SparqlAnalyzer.transform_with_clause_to_subquery(query)
        self.assertEqual(expected_query, fixed_query)
        self.assertFalse(SparqlAnalyzer.is_valid(query))
        self.assertTrue(fixed_query)

    def test_transform_with_clause_to_subquery_simple_example(self):
        """
        test transform_with_clause_to_subquery with a simple example
        """
        query = """
SELECT ?country ?label WITH {
  SELECT ?country WHERE {
    wd:Q27230297 wdt:P495 ?country
  }
} AS %MOLS {
  INCLUDE %MOLS
  OPTIONAL { ?country rdfs:label ?label. FILTER(LANG(?label)="en") }
}
        """
        self.assertTrue(SparqlAnalyzer.has_blazegraph_with_clause(query))
        fixed_query = SparqlAnalyzer.transform_with_clause_to_subquery(query)
        print(fixed_query)
        self.assertFalse(SparqlAnalyzer.is_valid(query))
        self.assertTrue(fixed_query)

    def test_handling_of_parametrized_query(self):
        """
        tests handling of parametrized query
        """
        sparql = """
ASK {
    [] pq:P3712 / wdt:P31 wd:Q96471816 ; ps:P2860 / wdt:P1433 wd:{{q}} . BIND("venue-cito" AS ?aspectsubpage)
}
        """
        has_parameter = SparqlAnalyzer.has_parameter(sparql)
        self.assertTrue(has_parameter)
        expected_params = {"q"}
        query_params = SparqlAnalyzer.get_query_parameter(sparql)
        self.assertSetEqual(expected_params, query_params)
        filled_query = SparqlAnalyzer.fill_with_sample_query_parameters(sparql)
        prefixed_filled_query = SparqlAnalyzer.add_missing_prefixes(filled_query)
        self.assertTrue(SparqlAnalyzer.is_valid(prefixed_filled_query))

    def test_transform_with_clause_to_subquery_with_multiple_clauses(self):
        query = """
#title: Variants of author name strings
PREFIX target: <http://www.wikidata.org/entity/{{ q }}>

SELECT 
  (COUNT(?work) AS ?count)
  ?string
  (CONCAT("https://author-disambiguator.toolforge.org/names_oauth.php?doit=Look+for+author&name=", 
        ENCODE_FOR_URI(?string)) AS ?author_resolver_url) 
WITH
{
  # Find strings associated with the target author
  SELECT DISTINCT ?string_
  WHERE
  {
    { target: rdfs:label ?string_. } # in label
    UNION
    { target: skos:altLabel ?string_. } # in alias
    UNION
    {
      ?author_statement ps:P50 target: ; 
                        pq:P1932 ?string_. # in "stated as" strings for "author" statements on work items
    }
  }
} AS %RAWstrings
WITH
# This part is due to Dipsacus fullonum, as per https://w.wiki/5Brk
{
  # Calculate capitalization variants of these raw strings
  SELECT DISTINCT ?string
  WHERE
  {
    {
      INCLUDE %RAWstrings
      BIND(STR(?string_) AS ?string) # the raw strings
    }
    UNION
    {
      INCLUDE %RAWstrings
      BIND(UCASE(STR(?string_)) AS ?string) # uppercased versions of the raw strings
    }
    UNION
    {
      INCLUDE %RAWstrings
      BIND(LCASE(STR(?string_)) AS ?string) # lowercased versions of the raw strings
    }
  }
} AS %NORMALIZEDstrings
WHERE {
  # Find works that have "author name string" values equal to these normalized strings
  INCLUDE %NORMALIZEDstrings
  OPTIONAL { ?work wdt:P2093 ?string. }
}
GROUP BY ?string
ORDER BY DESC (?count)

        """
        fixed_query = SparqlAnalyzer.add_missing_prefixes(query)
        if SparqlAnalyzer.has_parameter(fixed_query):
            fixed_query = SparqlAnalyzer.fill_with_sample_query_parameters(fixed_query)
        if SparqlAnalyzer.has_blazegraph_with_clause(fixed_query):
            fixed_query = SparqlAnalyzer.transform_with_clause_to_subquery(fixed_query)
        is_valid = SparqlAnalyzer.is_valid(fixed_query)
        self.assertTrue(is_valid)

    def test_detect_undefined_prefixes(self):
        """
        Test detection for undefined prefixes.
        """
        query = "SELECT * WHERE {?work undefined:P2093 ?work . }"
        with self.assertLogs(snapquery.sparql_analyzer.logger, level="INFO") as cm:
            SparqlAnalyzer.add_missing_prefixes(query)
            self.assertIn(
                "ERROR:snapquery.sparql_analyzer:Prefix definitions missing for: {'undefined'} → Not all prefixes that are missing can be added",
                cm.output,
            )

    def test_add_missing_prefixes_on_incorreect_query(self):
        """
        Test add_missing_prefixes on query with syntax error making parsing impossible
        """
        query = "SELET * WHERE {??work undefined:P2093 ?work . }"
        with self.assertLogs(snapquery.sparql_analyzer.logger, level=logging.DEBUG) as cm:
            SparqlAnalyzer.add_missing_prefixes(query)
            self.assertIn(
                "DEBUG:snapquery.sparql_analyzer:Adding missing prefixes to query failed → Unable to parse SPARQL query",
                cm.output,
            )

    def test_fill_with_sample_query_parameters_with_parameterless_query(self):
        """
        Test fill_with_sample_query_parameters with parameterless query.
        """
        query = "SELECT * WHERE {?work undefined:P2093 ?work . }"
        filled_query = SparqlAnalyzer.fill_with_sample_query_parameters(query)
        self.assertEqual(filled_query, query)

    @unittest.skip("Only for manual inspection of the parameter name distribution")
    def test_scholia_param_name_distro(self):
        """
        Extract the distribution of scholia param names
        """
        nqm = NamedQueryManager()
        namespaces = [
            (
                "scholia.toolforge.org",
                "named_queries",
            )  # all queries works except one which expects a datetime parameter which is not detected
        ]
        params: dict[str, int] = dict()
        params["Has no parameter"] = 0
        for domain, namespace in namespaces:
            queries = nqm.get_all_queries(namespace=namespace, domain=domain)
            for query in queries:
                query_params = SparqlAnalyzer.get_query_parameter(query.sparql)
                if query_params:
                    for param in query_params:
                        if param in params:
                            params[param] += 1
                        else:
                            params[param] = 1
                else:
                    params["Has no parameter"] += 1
        pprint.pprint(params)


if __name__ == "__main__":
    unittest.main()
