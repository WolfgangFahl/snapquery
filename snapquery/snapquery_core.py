"""
Created on 2024-05-03

@author: wf
"""

import json
import os
import re
import uuid
import datetime
from dataclasses import field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import requests
from lodstorage.csv import CSV
from lodstorage.query import Endpoint, EndpointManager, Format, Query
from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB, EntityInfo
from lodstorage.yamlable import lod_storable
from ngwidgets.widgets import Link

@lod_storable
class QueryStats:
    """
    statistics about a query
    """
    stats_id: str = field(init=False)
    query_id: str # foreign key
    endpoint_name: str # foreign key
    time_stamp: datetime.datetime = field(init=False)
    duration: float = field(init=False, default=None)  # duration in seconds
    error_msg: Optional[str]=None
    
    def __post_init__(self):
        """
        Post-initialization processing to construct a unique identifier for the query
        and record the timestamp when the query stats object is created.
        """
        self.stats_id = str(uuid.uuid4())
        self.time_stamp = datetime.datetime.now()

    def done(self):
        """
        Set the duration by calculating the elapsed time since the `time_stamp`.
        """
        self.duration = (datetime.datetime.now() - self.time_stamp).total_seconds()

    def as_record(self) -> Dict:
        record = {}
        for field in fields(self):
            # Include field in the record dictionary if it has already been initialized (i.e., not None or has default)
            if hasattr(self, field.name):
                record[field.name] = getattr(self, field.name)
        return record
    
    @classmethod
    def get_samples(cls) -> dict[str, "QueryStats"]:
        """
        get samples
        """
        samples = {
            "wikidata-examples": [
                QueryStats(
                    query_id="wikidata-examples.cats",
                    endpoint_name="wikidata",
                )
            ]
        }
        # Set the duration for each sample instance
        for sample_list in samples.values():
            for sample in sample_list:
                sample.duration = 0.5
        return samples
                
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
    # sparql query (to be hidden later)
    sparql: str
    # the url of the source code of the query
    url: Optional[str] = None
    # one line title
    title: Optional[str] = None
    # multiline description
    description: Optional[str] = None

    def __post_init__(self):
        """
        Post-initialization processing to construct a unique identifier for the query
        based on its namespace and name.
        """
        self.query_id = f"{self.namespace}.{self.name}"
        
    @classmethod
    def get_samples(cls) -> dict[str, "NamedQuery"]:
        """
        get samples
        """
        samples = {
            "wikidata-examples": [
            NamedQuery(
                namespace="wikidata-examples",
                name="cats",
                url="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples#Cats",
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
            NamedQuery(
                namespace="wikidata-examples",
                name="horses",
                url="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples#Horses_(showing_some_info_about_them)",
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
            )
        ]
        }
        return samples

    def as_link(self) -> str:
        """
        get me as a link
        """
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
            title=record.get("title"),
            url=record.get("url"),
            description=record.get("description"),
            sparql=record.get("sparql"),
        )

    def as_record(self) -> Dict:
        record = {
            "namespace": self.namespace,
            "name": self.name,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "sparql": self.sparql,
        }
        return record

    def as_viewrecord(self) -> Dict:
        """
        Return a dictionary representing the NamedQuery with keys ordered as Name, Namespace, Title, Description.
        """
        url_link = Link.create(self.url, self.url)
        return {
            "name": self.as_link(),
            "namespace": self.namespace,
            "title": self.title,
            "description": self.description,
            "url": url_link,
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

    def raw_query(self, resultFormat, mime_type: str = None, timeout: float = 10.0):
        """
        returns raw result of the endpoint

        Args:
            resultFormat(str): format of the result
            mime_type(str): mime_type to use (if any)
            timeout(float): timeout in seconds

        Returns:
            raw result of the query
        """
        params = {"query": self.query.query, "format": resultFormat}
        payload = {}
        if mime_type:
            headers = {"Accept": mime_type}
        else:
            headers = {}
        endpoint_url = self.endpoint.endpoint
        method = self.endpoint.method
        response = requests.request(
            method,
            endpoint_url,
            headers=headers,
            data=payload,
            params=params,
            timeout=timeout,
        )
        return response.text

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

    def set_limit(self, limit: int = None):
        """
        set the limit of my query

        Args:
            limit(int): the limit to set - default: None
        """
        if limit:
            sparql_query = self.query.query
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
            for (source_class,pk) in [
                (NamedQuery,"query_id"),
                (QueryStats,"stats_id")
            ]:
                # Fetch sample records from the specified class
                sample_records = cls.get_sample_records(source_class=source_class)
            
                # Define entity information dynamically based on the class and primary key
                entityInfo = EntityInfo(
                    sample_records, name=source_class.__name__, primaryKey=pk
                )
            
                # Create and populate the table specific to each class
                nqm.sql_db.createTable(sample_records, source_class.__name__, withDrop=True)
                nqm.sql_db.store(sample_records, entityInfo)
        return nqm

    def store(self, lod: List[Dict[str, Any]], source_class: Type=NamedQuery, primary_key:str="query_id") -> None:
        """
        Stores the given list of dictionaries in the database using entity information
        derived from a specified source class.
    
        Args:
            lod (List[Dict[str, Any]]): List of dictionaries that represent the records to be stored.
            source_class (Type): The class from which the entity information is derived. This class
                should have an attribute or method that defines its primary key and must have a `__name__` attribute.
            primary_key(str): the primary key to use
        Raises:
            AttributeError: If the source class does not have the necessary method or attribute to define the primary key.
        """
        # Fetch sample records to define the structure of data and to extract entity information.
        sample_records = NamedQueryManager.get_sample_records(source_class=source_class)
        
        # Define entity information based on the source class
        entityInfo = EntityInfo(
            sample_records, name=source_class.__name__, primaryKey=primary_key
        )
        
        # Store the list of dictionaries in the database using the defined entity information
        self.sql_db.store(lod, entityInfo, fixNone=True, replace=True)

    @classmethod
    def get_sample_records(cls, source_class: Type) -> List[Dict[str, Any]]:
        """
        Generates a list of dictionary records based on the sample instances
        provided by a source class. This method utilizes the `get_samples` method
        of the source class, which should return a dictionary of sample instances.
    
        Args:
            source_class (Type): The class from which to fetch sample instances.
                This class must implement a `get_samples` method that returns
                a dictionary of instances categorized by some key.
    
        Returns:
            List[Dict[str, Any]]: A list of dictionaries where each dictionary
                is a record that corresponds to a sample instance from the source class.
    
        Raises:
            AttributeError: If the source_class does not have a `get_samples` method.
        """
        if not hasattr(source_class, "get_samples"):
            raise AttributeError(f"The class {source_class.__name__} must have a 'get_samples' method.")
    
        sample_instances = source_class.get_samples()
        list_of_records = []
    
        # Assuming each key in the returned dictionary of get_samples corresponds to a list of instances
        for instance_group in sample_instances.values():
            for instance in instance_group:
                # Ensure that the instance has an 'as_record' method to convert it to a dictionary
                if hasattr(instance, "as_record"):
                    record = instance.as_record()
                    list_of_records.append(record)
                else:
                    raise AttributeError(f"The instance of class {source_class.__name__} does not have an 'as_record' method.")
    
        return list_of_records


    def lookup(self, name: str, namespace: str) -> NamedQuery:
        """
        lookup the named query for the given name and namespace


        Args:
            name (str): The name of the named query to execute.
            namespace (str): The namespace of the named query, default is 'wikidata-examples'.

        Returns:
            NamedQuery: the named query
        """
        sql_query = """SELECT 
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
        if endpoint_name not in self.endpoints:
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
        query.tryItUrl = query.getTryItUrl(endpoint.website, endpoint.database)
        query.database = endpointConf.database
        query_bundle = QueryBundle(
            named_query=named_query, query=query, endpoint=endpoint
        )
        query_bundle.set_limit(limit)
        return query_bundle
