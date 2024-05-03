"""
Created on 2024-05-03

@author: wf
"""
import os
import json
from dataclasses import field
from pathlib import Path
from typing import Optional

from lodstorage.query import EndpointManager, Query, Format
from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB, EntityInfo
from lodstorage.yamlable import lod_storable
from lodstorage.csv import CSV

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
        self.sql_db = SQLDB(dbname=db_path, debug=debug)
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
    
    def get_sparql(self,name: str,
        namespace: str = "wikidata-examples",
        endpoint_name: str = "wikidata")->str:
        sql_query = f"""SELECT 
    sparql 
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

        sparql_query = query_records[0]["sparql"]
        return sparql_query

    def query(
        self,
        name: str,
        namespace: str = "wikidata-examples",
        endpoint_name: str = "wikidata",
    ):
        """
        Execute a named SPARQL query using a specified endpoint and return the results.

        Args:
            name (str): The name of the named query to execute.
            namespace (str): The namespace of the named query, default is 'wikidata-examples'.
            endpoint_name (str): The name of the endpoint to send the SPARQL query to, default is 'wikidata'.

        Returns:
            Dict[str, Any]: The results of the SPARQL query in JSON format.

        Raises:
            ValueError: If no named query matches the given name and namespace.
            Exception: If the SPARQL query execution fails or the endpoint returns an error.
        """
        sparql_query=self.get_sparql(name, namespace, endpoint_name)

        if not endpoint_name in self.endpoints:
            msg = f"Invalid endpoint {endpoint_name}"
            ValueError(msg)
        endpoint = self.endpoints.get(endpoint_name)
        sparql = SPARQL(endpoint.endpoint)
        lod = sparql.queryAsListOfDicts(sparql_query)
        return lod
    
    def format_result(self,qlod,query:Query,r_format:Format,endpoint_name: str = "wikidata"):
        """
        """
        endpointConf = self.endpoints.get(endpoint_name)
        query.tryItUrl = endpointConf.website
        query.database = endpointConf.database
    
        if r_format is Format.csv:
                csv = CSV.toCSV(qlod)
                print(csv)
        elif r_format in [Format.latex, Format.github, Format.mediawiki]:
                doc = query.documentQueryResult(
                    qlod, tablefmt=str(r_format), floatfmt=".0f"
                )
                docstr = doc.asText()
                print(docstr)
        elif r_format in [Format.json] or format is None:  # set as default
                # https://stackoverflow.com/a/36142844/1497139
                print(json.dumps(qlod, indent=2, sort_keys=True, default=str))
