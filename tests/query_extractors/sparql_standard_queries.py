import unittest
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from lodstorage.query import Query

from snapquery.query_annotate import SparqlQueryAnnotater
from snapquery.snapquery_core import NamedQuery, NamedQuerySet


class TestSparqlStandardExtraction(unittest.TestCase):
    """
    Holds extraction methods to extract and convert the queries in the SPARQL standard
    """

    def extracting_sparql_11(self):
        url = "https://www.w3.org/TR/sparql11-query/"
        req = Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        html_page = urlopen(req).read()
        soup = BeautifulSoup(html_page, "html.parser")
        query_elements = soup.find_all("pre", {"class": "query"})
        queries = []
        for element in query_elements:
            header = element.findPrevious(["h1", "h2", "h3", "h4", "h5", "h6"])

            classes = element.attrs["class"]
            if "untested" in classes:
                continue
            elif "add" in classes:
                continue
            print(header.text)
            query = element.text
            queries.append(Query(name=header.text, query=query))
        print(len(queries))
        print(classes)
        return queries

    @unittest.skip("")
    def test_extracting_sparql_11(self):
        queries = self.extracting_sparql_11()
        query_set = NamedQuerySet(
            domain="w3.org", namespace="sparql_1.1", target_graph_name=""
        )
        for query in queries:
            named_query = NamedQuery(
                title=query.name,
                sparql=query.query,
                namespace=query_set.namespace,
                domain=query_set.domain,
                name=query.name,
            )
            query_set.add(named_query)
        json_str = query_set.to_json()
        print(json_str)

    @unittest.skip("")
    def test_evaluation_sparql_11(self):
        queries = self.extracting_sparql_11()
        functions = []
        keywords = []
        for query in queries:
            annotated_query = SparqlQueryAnnotater(query)
            functions.extend(annotated_query.get_used_functions())
            keywords.extend(annotated_query.get_used_keywords())
        print(sorted(set(functions)))


if __name__ == "__main__":
    unittest.main()
