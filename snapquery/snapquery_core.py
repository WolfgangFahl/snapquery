"""
Created on 2024-05-03

@author: wf
"""
import json
import os
import re
from dataclasses import field
from pathlib import Path
from typing import Any, Dict, List, Optional

from lodstorage.csv import CSV
from lodstorage.query import Endpoint, EndpointManager, Format, Query
from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB, EntityInfo
from lodstorage.yamlable import lod_storable
from ngwidgets.widgets import Link


@lod_storable
class NamedQuery:
    """
    A named query that encapsulates the details and SPARQL query for a specific purpose.

    Attributes:
        namespace (str): The namespace of the query, which helps in categorizing the query.
        name (str): The unique name or identifier of the query within its namespace.
        title (str): A brief one-line title that describes the query.
        description (str): A detailed multiline description of what the query does and the data it accesses.
        sparql (str): The SPARQL query string. This might be hidden in future to encapsulate query details.
        query_id (str): A unique identifier for the query, generated from namespace and name, used as a primary key.
    """
    query_id: str = field(init=False)

    # namespace
    namespace: str
    # name/id
    name: str
    # one line title
    title: str
    # multiline description
    description: str
    # sparql query (to be hidden later)
    sparql: str

    def __post_init__(self):
        """
        Post-initialization processing to construct a unique identifier for the query
        based on its namespace and name.
        """
        self.query_id = f"{self.namespace}.{self.name}"

    def as_link(self) -> str:
        url = f"/query/{self.namespace}/{self.name}"
        text = self.name
        tooltip = "query details"
        link = Link.create(url, text, tooltip)
        return link

    @classmethod
    def from_record(cls, record: Dict) -> "NamedQuery":
        """
        Class method to instantiate NamedQuery from a dictionary record.
        """
        return cls(
            namespace=record["namespace"],
            name=record["name"],
            title=record["title"],
            description=record["description"],
            sparql=record["sparql"],
        )

    def as_viewrecord(self) -> Dict:
        """
        Return a dictionary representing the NamedQuery with keys ordered as Name, Namespace, Title, Description.
        """
        return {
            "name": self.as_link(),
            "namespace": self.namespace,
            "title": self.title,
            "description": self.description,
        }


class QueryBundle:
    """
    Bundles a named query, a query, and an endpoint into a single manageable object, facilitating the execution of SPARQL queries.

    Attributes:
        named_query (NamedQuery): The named query object, which includes metadata about the query.
        query (Query): The actual query object that contains the SPARQL query string.
        endpoint (Endpoint): The endpoint object where the SPARQL query should be executed.
        sparql (SPARQL): A SPARQL service object initialized with the endpoint URL.
    """

    def __init__(self, named_query: NamedQuery, query: Query, endpoint: Endpoint):
        """
        Initializes a new instance of the QueryBundle class.

        Args:
            named_query (NamedQuery): An instance of NamedQuery that provides a named reference to the query.
            query (Query): An instance of Query containing the SPARQL query string.
            endpoint (Endpoint): An instance of Endpoint representing the SPARQL endpoint URL.
        """
        self.named_query = named_query
        self.query = query
        self.endpoint = endpoint
        self.sparql = SPARQL(endpoint.endpoint)

    def get_lod(self) -> List[dict]:
        """
        Executes the stored query using the SPARQL service and returns the results as a list of dictionaries.

        Returns:
            List[dict]: A list where each dictionary represents a row of results from the SPARQL query.
        """
        lod = self.sparql.queryAsListOfDicts(self.query.query)
        return lod

    def format_result(
        self,
        qlod: List[Dict[str, Any]] = None,
        r_format: Format = Format.json,
    ) -> Optional[str]:
        """
        Formats the query results based on the specified format and prints them.

        Args:
            qlod (List[Dict[str, Any]]): The list of dictionaries that represent the query results.
            query (Query): The query object which contains details like the endpoint and the database.
            r_format(Format): The format in which to print the results.

        Returns:
            Optional[str]: The formatted string representation of the query results, or None if printed directly.
        """
        if qlod is None:
            qlod = self.get_lod()
        if r_format is None:
            r_format = Format.json
        if r_format == Format.csv:
            csv_output = CSV.toCSV(qlod)
            return csv_output
        elif r_format in [Format.latex, Format.github, Format.mediawiki, Format.html]:
            doc = self.query.documentQueryResult(
                qlod, tablefmt=str(r_format), floatfmt=".0f"
            )
            return doc.asText()
        elif r_format == Format.json:
            return json.dumps(qlod, indent=2, sort_keys=True, default=str)
        return None  # In case no format is matched or needed

    def set_limit(self,limit:int=None):
        if limit:
            sparql_query=self.query.query
            # @TODO - this is too naive for cases where 
            # there are SPARQL elements hat have a "limit" in the name e.g. "height_limit"
            # or if there is a LIMIT in a subquery
            if "limit" in sparql_query or "LIMIT" in sparql_query:
                sparql_query = re.sub(
                    r"(limit|LIMIT)\s+(\d+)", f"LIMIT {limit}", sparql_query
                )
            else:
                sparql_query += f"\nLIMIT {limit}"
            self.query.query = sparql_query
            
class NamedQueryManager:
    """
    Manages the storage, retrieval, and execution of named SPARQL queries.
    """

    def __init__(self, db_path: str = None, debug: bool = False):
        """
        Initializes the NamedQueryManager with a specific database path and a debug mode.

        Args:
            db_path (Optional[str]): The file path to the SQLite database. If None, the default cache path is used.
            debug (bool): If True, enables debug mode which may provide additional logging and error reporting.

        Attributes:
            debug (bool): Stores the debug state.
            sql_db (SQLDB): An instance of SQLDB to manage the SQLite database interactions.
            endpoints (dict): A dictionary of SPARQL endpoints configured for use.
        """
        if db_path is None:
            db_path = NamedQueryManager.get_cache_path()
        self.debug = debug
        self.sql_db = SQLDB(dbname=db_path, check_same_thread=False, debug=debug)
        self.endpoints = EndpointManager.getEndpoints(lang="sparql")

    @classmethod
    def get_cache_path(cls) -> str:
        home = str(Path.home())
        cache_dir = f"{home}/.solutions/snapquery/storage"
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = f"{cache_dir}/named_queries.db"
        return cache_path

    @classmethod
    def from_samples(
        cls, db_path: Optional[str] = None, debug: bool = False
    ) -> "NamedQueryManager":
        """
        Creates and returns an instance of NamedQueryManager, optionally initializing it from sample data.

        Args:
            db_path (Optional[str]): Path to the database file. If None, the default path is used.
            debug (bool): If True, enables debug mode which may provide additional logging.

        Returns:
            NamedQueryManager: An instance of the manager initialized with the database at `db_path`.
        """
        if db_path is None:
            db_path = cls.get_cache_path()

        nqm = NamedQueryManager(debug=debug)
        path_obj = Path(db_path)
        if not path_obj.exists() or path_obj.stat().st_size == 0:
            sample_queries = cls.get_samples()
            list_of_records = []
            for _query_name, named_query in sample_queries.items():
                record = {
                    "namespace": named_query.namespace,
                    "name": named_query.name,
                    "title": named_query.title,
                    "description": named_query.description,
                    "sparql": named_query.sparql,
                }
                list_of_records.append(record)
            entityInfo = EntityInfo(
                list_of_records, name="NamedQuery", primaryKey="query_id"
            )
            nqm.sql_db.createTable(list_of_records, "NamedQuery", withDrop=True)
            nqm.sql_db.store(list_of_records, entityInfo)
        return nqm

    @classmethod
    def get_samples(cls) -> dict[str, NamedQuery]:
        """
        get samples
        """
        samples = {
            "wikidata-examples.cats": NamedQuery(
                namespace="wikidata-examples",
                name="cats",
                title="Cats on Wikidata",
                description="This query retrieves all items classified under 'house cat' (Q146) on Wikidata.",
                sparql="""
SELECT ?item ?itemLabel
WHERE {
  ?item wdt:P31 wd:Q146. # Must be a cat
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
""",
            ),
            "wikidata-examples.horses": NamedQuery(
                namespace="wikidata-examples",
                name="horses",
                title="Horses on Wikidata",
                description="This query retrieves information about horses, including parents, gender, and approximate birth and death years.",
                sparql="""
SELECT DISTINCT ?horse ?horseLabel ?mother ?motherLabel ?father ?fatherLabel 
(year(?birthdate) as ?birthyear) (year(?deathdate) as ?deathyear) ?genderLabel
WHERE {
  ?horse wdt:P31/wdt:P279* wd:Q726 .     # Instance and subclasses of horse (Q726)
  OPTIONAL{?horse wdt:P25 ?mother .}     # Mother
  OPTIONAL{?horse wdt:P22 ?father .}     # Father
  OPTIONAL{?horse wdt:P569 ?birthdate .} # Birth date
  OPTIONAL{?horse wdt:P570 ?deathdate .} # Death date
  OPTIONAL{?horse wdt:P21 ?gender .}     # Gender
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "[AUTO_LANGUAGE],fr,ar,be,bg,bn,ca,cs,da,de,el,en,es,et,fa,fi,he,hi,hu,hy,id,it,ja,jv,ko,nb,nl,eo,pa,pl,pt,ro,ru,sh,sk,sr,sv,sw,te,th,tr,uk,yue,vec,vi,zh"
  }
}
ORDER BY ?horse
""",
            ),
        }
        return samples

    def lookup(self, name: str, namespace: str) -> NamedQuery:
        """
        lookup the named query for the given name and namespace


        Args:
            name (str): The name of the named query to execute.
            namespace (str): The namespace of the named query, default is 'wikidata-examples'.

        Returns:
            NamedQuery: the named query
        """
        sql_query = f"""SELECT 
    *
FROM 
    NamedQuery 
WHERE 
    name = ? AND namespace = ?"""
        query_records = self.sql_db.query(sql_query, (name, namespace))

        if not query_records:
            msg = f"NamedQuery not found for the specified name '{name}' and namespace '{namespace}'."
            raise ValueError(msg)

        query_count = len(query_records)
        if query_count != 1:
            msg = f"multiple entries ({query_count}) for name '{name}' and namespace '{namespace}'"
            raise ValueError(msg)

        record = query_records[0]
        named_query = NamedQuery.from_record(record)
        return named_query

    def get_query(
        self,
        name: str,
        namespace: str = "wikidata-examples",
        endpoint_name: str = "wikidata",
        limit: int = None,
    ) -> QueryBundle:
        """
        get the query for the given parameters

        Args:
            name (str): The name of the named query to execute.
            namespace (str): The namespace of the named query, default is 'wikidata-examples'.
            endpoint_name (str): The name of the endpoint to send the SPARQL query to, default is 'wikidata'.
            limit(int): the query limit (if any)

        Returns:
            QueryBundle: named_query, query and endpoint
        """
        named_query = self.lookup(name, namespace)
        if not endpoint_name in self.endpoints:
            msg = f"Invalid endpoint {endpoint_name}"
            ValueError(msg)
        endpoint = self.endpoints.get(endpoint_name)
        sparql_query = named_query.sparql
        query = Query(
            name=name,
            query=sparql_query,
            lang="sparql",
            endpoint=endpoint.endpoint,
            limit=limit,
        )
        endpointConf = self.endpoints.get(endpoint_name, Endpoint.getDefault())
        query.tryItUrl = endpointConf.website
        query.database = endpointConf.database
        query_bundle = QueryBundle(
            named_query=named_query, query=query, endpoint=endpoint
        )
        query_bundle.set_limit(limit)
        return query_bundle
