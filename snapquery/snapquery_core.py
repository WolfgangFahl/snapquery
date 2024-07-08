"""
Created on 2024-05-03

@author: wf
"""

import datetime
import json
import logging
import os
import re
import urllib.parse
import uuid
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

import requests
from lodstorage.lod_csv import CSV
from lodstorage.params import Params
from lodstorage.query import Endpoint, EndpointManager, Format, Query, QueryManager
from lodstorage.sparql import SPARQL
from lodstorage.sql import SQLDB, EntityInfo
from lodstorage.yamlable import lod_storable
from ngwidgets.widgets import Link
from snapquery.sparql_analyzer import SparqlAnalyzer

from snapquery.endpoint import Endpoint as SnapQueryEndpoint
from snapquery.error_filter import ErrorFilter
from snapquery.graph import Graph, GraphManager

logger = logging.getLogger(__name__)


@lod_storable
class QueryStats:
    """
    statistics about a query
    """

    stats_id: str = field(init=False)
    query_id: str  # foreign key
    endpoint_name: str  # foreign key

    context: Optional[str] = None  # a context for the query stats
    records: Optional[int] = None
    time_stamp: datetime.datetime = field(init=False)
    duration: Optional[float] = field(init=False, default=None)  # duration in seconds
    error_msg: Optional[str] = None
    error_category: Optional[str] = None

    filtered_msg: Optional[str] = None

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

    def apply_error_filter(self, for_html: bool = False) -> ErrorFilter:
        """
        Applies an error filter to the error message and sets the filtered message.

        Args:
            for_html (bool): If True, formats the message for HTML output.

        Returns:
            ErrorFilter: the error filter that has been applied
        """
        error_filter = ErrorFilter(self.error_msg)
        self.filtered_msg = error_filter.get_message(for_html=for_html)
        self.error_category = error_filter.category
        return error_filter

    def error(self, ex: Exception):
        """
        Handle exception of query
        """
        self.duration = None
        self.error_msg = str(ex)
        self.apply_error_filter()

    @classmethod
    def from_record(cls, record: Dict) -> "QueryStats":
        """
        Class method to instantiate NamedQuery
        from a dictionary record.
        """
        stat = cls(
            query_id=record.get("query_id", None),
            endpoint_name=record.get("endpoint_name", None),
            records=record.get("records", None),
            error_msg=record.get("error_msg", None),
        )
        stat.stats_id = record.get("stats_id", stat.stats_id)
        stat.time_stamp = record.get("time_stamp", stat.time_stamp)
        stat.duration = record.get("duration", None)
        return stat

    def as_record(self) -> Dict:
        """
        convert my declared attributes to a dict
        @TODO may be use asdict from dataclasses instead?
        """
        record = {}
        for _field in fields(self):
            # Include field in the record dictionary if it has already been initialized (i.e., not None or has default)
            if hasattr(self, _field.name):
                record[_field.name] = getattr(self, _field.name)
        return record

    @classmethod
    def get_samples(cls) -> dict[str, "QueryStats"]:
        """
        get samples for QueryStats
        """
        samples = {
            "snapquery-examples": [
                cls(
                    query_id="horses--snapquery-examples@wikidata.org",
                    endpoint_name="wikidata",
                    context="samples",
                    records=0,
                    error_msg="HTTP Error 504: Query has timed out.",
                    filtered_msg="Timeout: HTTP Error 504: Query has timed out.",
                    error_category="Timeout",
                ),
                cls(
                    query_id="cats--snapquery-examples@wikidata.org",
                    endpoint_name="wikidata",
                    context="samples",
                    records=223,
                    error_msg="",
                    error_category=None,
                    filtered_msg="",
                ),
            ]
        }
        # Set the duration for each sample instance
        for sample_list in samples.values():
            for sample in sample_list:
                sample.duration = 0.5
        return samples

    def is_successful(self) -> bool:
        """
        Returns True if the query was successful
        """
        return self.duration and self.error_msg is None


@lod_storable
class QueryName:
    """
    A structured query name with a fully qualifying query id that is URL-friendly
    Attributes:
        domain(str): the domain of the owner of this namespace
        namespace (str): The namespace of the query, which helps in categorizing the query.
        name (str): The unique name or identifier of the query within its namespace.
        query_id(str): encoded id e.g. cats--examples@wikidata.org
    """

    # name
    name: str
    # namespace
    namespace: str = "examples"
    # domain
    domain: str = "wikidata.org"
    # query_id
    query_id: str = field(init=False)

    def __post_init__(self):
        self.query_id = self.get_query_id(self.name, self.namespace, self.domain)

    @classmethod
    def get_query_id(cls, name: str, namespace: str, domain: str) -> str:
        """
        Generate a URL-friendly query_id
        """
        # Convert None to empty string (or use any other default logic)
        name, namespace, domain = (name or ""), (namespace or ""), (domain or "")

        encoded_name = urllib.parse.quote(name, safe="")
        encoded_namespace = urllib.parse.quote(namespace, safe="")
        encoded_domain = urllib.parse.quote(domain, safe="")
        query_id = f"{encoded_name}--{encoded_namespace}@{encoded_domain}"
        # query_id=query_id.lower()
        return query_id

    @classmethod
    def from_query_id(
        cls,
        query_id: str,
        namespace: str = "examples",  # default namespace
        domain: str = "wikidata.org",  # default domain
    ) -> "QueryName":
        """
        Parse a URL-friendly query_id string into a QueryName object.
        Args:
            query_id (str): The URL-friendly query_id string to parse.
            namespace (str): Default namespace if not specified in query_id
            domain (str): Default domain if not specified in query_id
        Returns:
            QueryName: A QueryName object containing name, namespace, and domain.
        """
        parts = query_id.split("--")
        name = urllib.parse.unquote(parts[0])

        if len(parts) > 1:
            ns_domain = parts[1].split("@")
            namespace = urllib.parse.unquote(ns_domain[0])
            if len(ns_domain) > 1:
                domain = urllib.parse.unquote(ns_domain[1])
        return cls(name=name, namespace=namespace, domain=domain)

    def to_dict(self) -> dict:
        """
        Convert the QueryName object to a dictionary
        """
        return {
            "name": self.name,
            "namespace": self.namespace,
            "domain": self.domain,
            "query_id": self.query_id,
        }


@dataclass
class NamedQuery(QueryName):
    """
    A named query that encapsulates the details and SPARQL query for a specific purpose.

    Attributes:
        title (str): A brief one-line title that describes the query.
        description (str): A detailed multiline description of what the query does and the data it accesses.
        sparql (str): The SPARQL query string. This might be hidden in future to encapsulate query details.
        query_id (str): A unique identifier for the query, generated from namespace and name, used as a primary key.
    """

    # sparql query (to be hidden later)
    sparql: Optional[str] = None
    # the url of the source code of the query
    url: Optional[str] = None
    # one line title
    title: Optional[str] = None
    # multiline description
    description: Optional[str] = None
    comment: Optional[str] = None

    @classmethod
    def get_samples(cls) -> dict[str, "NamedQuery"]:
        """
        get samples
        """
        samples = {
            "snapquery-examples": [
                NamedQuery(
                    domain="wikidata.org",
                    namespace="snapquery-examples",
                    name="cats",
                    url="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples#Cats",
                    title="Cats on Wikidata",
                    description="This query retrieves all items classified under 'house cat' (Q146) on Wikidata.",
                    comment="modified cats query from wikidata-examples",
                    sparql="""# snapquery cats example
SELECT ?item ?itemLabel
WHERE {
  ?item wdt:P31 wd:Q146. # Must be a cat
  OPTIONAL { ?item rdfs:label ?itemLabel. }
  FILTER (LANG(?itemLabel) = "en")
}
""",
                ),
                NamedQuery(
                    domain="wikidata.org",
                    namespace="snapquery-examples",
                    name="bands",
                    title="Rock bands",
                    url="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples#Rock_bands_that_start_with_%22M%22",
                    description="""Rock bands that start with "M" """,
                    comment="",
                    sparql="""SELECT ?band ?bandLabel
WHERE {
  ?band wdt:P31 wd:Q5741069.
  ?band rdfs:label ?bandLabel.
  FILTER(LANG(?bandLabel)="en").
  FILTER(STRSTARTS(?bandLabel,"M")).
}""",
                ),
                NamedQuery(
                    domain="wikidata.org",
                    namespace="snapquery-examples",
                    name="horses",
                    url="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples#Horses_(showing_some_info_about_them)",
                    title="Horses on Wikidata",
                    description="This query retrieves information about horses, including parents, gender, and approximate birth and death years.",
                    sparql="""# snapquery example horses
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
""",
                ),
            ]
        }
        return samples

    def as_link(self) -> str:
        """
        get me as a link
        """
        url = f"/query/{self.domain}/{self.namespace}/{self.name}"
        text = self.name
        tooltip = "query details"
        link = Link.create(url, text, tooltip)
        return link

    @classmethod
    def from_record(cls, record: Dict) -> "NamedQuery":
        """
        Class method to instantiate NamedQuery
        from a dictionary record.
        """
        return cls(
            domain=record["domain"],
            namespace=record["namespace"],
            name=record["name"],
            title=record.get("title"),
            url=record.get("url"),
            description=record.get("description"),
            sparql=record.get("sparql"),
        )

    def as_record(self) -> Dict:
        record = {
            "query_id": self.query_id,
            "domain": self.domain,
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
            "domain": self.domain,
            "namespace": self.namespace,
            "name": self.as_link(),
            "title": self.title,
            "url": url_link,
        }


@lod_storable
class QueryDetails:
    """
    Details for a named query
    """

    query_id: str
    params: str
    param_count: int
    lines: int
    size: int

    @classmethod
    def from_sparql(cls, query_id: str, sparql: str) -> "QueryDetails":
        """
        Creates an instance of QueryDetails from a SPARQL query string.

        This method parses the SPARQL query to determine the number of lines and the size of the query.
        It also identifies and lists the parameters used within the SPARQL query.

        Args:
            query_id (str): The identifier of the query.
            sparql (str): The SPARQL query string from which to generate the query details.

        Returns:
            QueryDetails: An instance containing details about the SPARQL query.
        """
        # Calculate the number of lines and the size of the sparql string
        lines = sparql.count("\n") + 1
        size = len(sparql.encode("utf-8"))

        # Example to extract parameters - this may need to be replaced with actual parameter extraction logic
        sparql_params = Params(
            query=sparql
        )  # Assuming Params is a class that can parse SPARQL queries to extract parameters
        params = ",".join(sparql_params.params) if sparql_params.params else None
        param_count = len(sparql_params.params)

        # Create and return the QueryDetails instance
        return cls(
            query_id=query_id,
            params=params,
            param_count=param_count,
            lines=lines,
            size=size,
        )

    @classmethod
    def get_samples(cls) -> dict[str, "QueryDetails"]:
        """
        get samples
        """
        samples = {
            "snapquery-examples": [
                QueryDetails(
                    query_id="scholia.test", params="q", param_count=1, lines=1, size=50
                )
            ]
        }
        return samples


@lod_storable
class QueryStatsList:
    """
    a list of query statistics
    """

    name: str  # the name of the list
    stats: List[QueryStats] = field(default_factory=list)


@lod_storable
class NamedQuerySet:
    """
    a list/set of named queries which defines a namespace
    """

    domain: str  # the domain of this NamedQuerySet
    namespace: str  # the namespace

    target_graph_name: str  # the name of the target graph
    queries: List[NamedQuery] = field(default_factory=list)

    def __len__(self):
        return len(self.queries)


class QueryBundle:
    """
    Bundles a named query, a query, and an endpoint into a single manageable object, facilitating the execution of SPARQL queries.

    Attributes:
        named_query (NamedQuery): The named query object, which includes metadata about the query.
        query (Query): The actual query object that contains the SPARQL query string.
        endpoint (Endpoint): The endpoint object where the SPARQL query should be executed.
        sparql (SPARQL): A SPARQL service object initialized with the endpoint URL.
    """

    def __init__(
        self, named_query: NamedQuery, query: Query, endpoint: Endpoint = None
    ):
        """
        Initializes a new instance of the QueryBundle class.

        Args:
            named_query (NamedQuery): An instance of NamedQuery that provides a named reference to the query.
            query (Query): An instance of Query containing the SPARQL query string.
            endpoint (Endpoint): An instance of Endpoint representing the SPARQL endpoint URL.
        """
        self.named_query = named_query
        self.query = query
        self.update_endpoint(endpoint)

    def update_endpoint(self, endpoint):
        self.endpoint = endpoint
        if endpoint:
            self.sparql = SPARQL(endpoint.endpoint, method=self.endpoint.method)

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

    def get_lod_with_stats(self) -> tuple[list[dict], QueryStats]:
        """
        Executes the stored query using the SPARQL service and returns the results as a list of dictionaries.

        Returns:
            List[dict]: A list where each dictionary represents a row of results from the SPARQL query.
        """
        logger.info(f"Querying {self.endpoint.name} with query {self.named_query.name}")
        query_stat = QueryStats(
            query_id=self.named_query.query_id, endpoint_name=self.endpoint.name
        )
        try:
            lod = self.sparql.queryAsListOfDicts(self.query.query)
            query_stat.records = len(lod) if lod else -1
            query_stat.done()
        except Exception as ex:
            lod = []
            logger.debug(f"Execution of query failed: {ex}")
            query_stat.error(ex)
        return (lod, query_stat)

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
                qlod, tablefmt=str(r_format), floatfmt=".1f"
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


class QueryPrefixMerger(Enum):
    """
    SPARQL Query prefix merger
    """
    RAW = "raw"
    SIMPLE_MERGER = "simple merger"
    ANALYSIS_MERGER = "analysis merger"

    @classmethod
    def _missing_(cls, key):
        return cls.default_merger()

    @classmethod
    def default_merger(cls) -> "QueryPrefixMerger":
        return cls.SIMPLE_MERGER

    @classmethod
    def merge_prefixes(cls, named_query: NamedQuery, query: Query, endpoint: Endpoint,
                       merger: "QueryPrefixMerger") -> str:
        """
        Merge prefixes with the given merger
        Args:
            named_query:
            query:
            endpoint:
            merger:

        Returns:
            merged query
        """
        if merger == QueryPrefixMerger.RAW:
            return query.query
        elif merger == QueryPrefixMerger.SIMPLE_MERGER:
            return cls.simple_prefix_merger(query.query, endpoint)
        elif merger == QueryPrefixMerger.ANALYSIS_MERGER:
            return cls.analysis_prefix_merger(query.query)
        else:
            return query.query

    @classmethod
    def simple_prefix_merger(cls, query_str: str, endpoint: Endpoint) -> str:
        """
        Simple prefix merger
        Args:
            query_str:
            endpoint:

        Returns:
            merged query
        """
        prefixes = endpoint.prefixes if hasattr(endpoint, "prefixes") else None
        merged_query = query_str
        if prefixes:
            merged_query = f"{prefixes}\n{merged_query}"
        return merged_query

    @classmethod
    def analysis_prefix_merger(cls, query_str: str) -> str:
        """
        Analysis prefix merger
        Args:
            query_str

        Returns:
            merged query
        """
        merged_query = SparqlAnalyzer.add_missing_prefixes(query_str)
        return merged_query


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
        # Get the path of the yaml_file relative to the current Python module
        self.samples_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "samples"
        )
        endpoints_path = os.path.join(self.samples_path, "endpoints.yaml")
        self.endpoints = EndpointManager.getEndpoints(
            endpointPath=endpoints_path, lang="sparql", with_default=False
        )
        yaml_path = os.path.join(self.samples_path, "meta_query.yaml")
        self.meta_qm = QueryManager(
            queriesPath=yaml_path, with_default=False, lang="sql"
        )
        # Graph Manager
        gm_yaml_path = GraphManager.get_yaml_path()
        self.gm = GraphManager.load_from_yaml_file(gm_yaml_path)
        # SQL meta data handling
        # primary keys
        self.primary_keys = {
            QueryStats: "stats_id",
            NamedQuery: "query_id",
            QueryDetails: "query_id",
        }
        self.entity_infos = {}
        pass

    @classmethod
    def get_cache_path(cls) -> str:
        home = str(Path.home())
        cache_dir = f"{home}/.solutions/snapquery/storage"
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = f"{cache_dir}/named_queries.db"
        return cache_path

    @classmethod
    def from_samples(
        cls,
        db_path: Optional[str] = None,
        force_init: bool = False,
        with_backup: bool = True,
        debug: bool = False,
    ) -> "NamedQueryManager":
        """
        Creates and returns an instance of NamedQueryManager, optionally initializing it from sample data.

        Args:
            db_path (Optional[str]): Path to the database file. If None, the default path is used.
            force_init (bool): If True, the existing database file is dropped and recreated, and backed up if with_backup is True.
            with_backup (bool): If True and force_init is True, moves the database file to a backup location before reinitialization.
            debug (bool): If True, enables debug mode which may provide additional logging.

        Returns:
            NamedQueryManager: An instance of the manager initialized with the database at `db_path`.
        """
        if db_path is None:
            db_path = cls.get_cache_path()

        path_obj = Path(db_path)

        # Handle backup and force initialization
        if force_init and path_obj.exists():
            if with_backup:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
                backup_path = path_obj.with_name(
                    f"{path_obj.stem}-{timestamp}{path_obj.suffix}"
                )
                path_obj.rename(backup_path)  # Move the existing file to backup

        nqm = NamedQueryManager(db_path=db_path, debug=debug)
        if force_init or not path_obj.exists() or path_obj.stat().st_size == 0:
            for source_class, pk in [
                (NamedQuery, "query_id"),
                (QueryStats, "stats_id"),
                (QueryDetails, "quer_id"),
            ]:
                # Fetch sample records from the specified class
                sample_records = cls.get_sample_records(source_class=source_class)

                # Define entity information dynamically based on the class and primary key
                entityInfo = EntityInfo(
                    sample_records, name=source_class.__name__, primaryKey=pk
                )

                # Create and populate the table specific to each class
                nqm.sql_db.createTable(
                    sample_records, source_class.__name__, withDrop=True
                )
                nqm.sql_db.store(sample_records, entityInfo, fixNone=True, replace=True)
            # store yaml defined entities to SQL database
            nqm.store_endpoints()
            nqm.store_graphs()
        return nqm

    def store_named_query_list(self, nq_set: NamedQuerySet):
        """
        store the given named query set

        Args:
            nq_list: NamedQueryList
        """
        lod = []
        for nq in nq_set.queries:
            lod.append(asdict(nq))
        self.store(lod=lod)

    def store_query_details_list(self, qd_list: List[QueryDetails]):
        """
        Stores a list of QueryDetails instances into the database. This function converts
        each QueryDetails instance into a dictionary and then stores the entire list of dictionaries.
        It utilizes the 'store' method to handle database operations based on the entity information
        derived from the QueryDetails class.

        Args:
            qd_list (List[QueryDetails]): List of QueryDetails instances to be stored.
        """
        qd_lod = []
        for qd in qd_list:
            qd_lod.append(asdict(qd))
        self.store(lod=qd_lod, source_class=QueryDetails)

    def store_stats(self, stats_list: List[QueryStats]):
        """
        store the given list of query statistics
        """
        stats_lod = []
        for stats in stats_list:
            stats_lod.append(asdict(stats))
        self.store(lod=stats_lod, source_class=QueryStats)

    def store_graphs(self, gm: GraphManager = None):
        """
        Stores all graphs managed by the given GraphManager into my
        SQL database
        """
        if gm is None:
            gm = self.gm

        lod = [
            asdict(graph) for graph in gm
        ]  # Convert each Graph instance to a dictionary using asdict()

        self.store(lod=lod, source_class=Graph, with_create=True)

    def store_endpoints(self, endpoints: Optional[Dict[str, Endpoint]] = None):
        """
        Stores the given endpoints or self.endpoints into the SQL database.

        Args:
            endpoints (Optional[Dict[str, LODStorageEndpoint]]): A dictionary of endpoints to store.
                If None, uses self.endpoints.
        """
        # This is a compatiblity layer for pylodstorage Endpoints
        # as of 2024-06 pylodstorage Endpoint still uses @Jsonable which is
        # deprecated so we convert instances to our local endpoint modules Endpoint format
        # and use our store mechanism to create SQL records
        if endpoints is None:
            endpoints = self.endpoints

        endpoints_lod = []
        for endpoint_name, lod_endpoint in endpoints.items():
            # Create a dictionary with only the attributes that exist in lod_endpoint
            endpoint_dict = {
                "name": endpoint_name,
                "lang": getattr(lod_endpoint, "lang", None),
                "endpoint": getattr(lod_endpoint, "endpoint", None),
                "website": getattr(lod_endpoint, "website", None),
                "database": getattr(lod_endpoint, "database", None),
                "method": getattr(lod_endpoint, "method", None),
                "prefixes": getattr(lod_endpoint, "prefixes", None),
                "auth": getattr(lod_endpoint, "auth", None),
                "user": getattr(lod_endpoint, "user", None),
                "password": getattr(lod_endpoint, "password", None),
            }

            # Remove None values
            endpoint_dict = {k: v for k, v in endpoint_dict.items() if v is not None}

            # Create SnapQueryEndpoint instance with only the available attributes
            snap_endpoint = SnapQueryEndpoint(**endpoint_dict)
            endpoints_lod.append(asdict(snap_endpoint))

        # Store the list of dictionaries in the database
        self.store(lod=endpoints_lod, source_class=SnapQueryEndpoint, with_create=True)

    def execute_query(
        self,
        named_query: NamedQuery,
        params_dict: Dict,
        endpoint_name: str = "wikidata",
        limit: int = None,
        with_stats: bool = True,
        prefix_merger: QueryPrefixMerger = QueryPrefixMerger.SIMPLE_MERGER
    ):
        """
        execute the given named_query

        Args:
            named_query(NamedQuery): the query to execute
            params_dict(Dict): the query parameters to apply (if any)
            endpoint_name(str): the endpoint where to the excute the query
            limit(int): the record limit for the results (if any)
            with_stats(bool): if True run the stats
            prefix_merger: prefix merger to use
        """
        # Assemble the query bundle using the named query, endpoint, and limit
        query_bundle = self.as_query_bundle(named_query, endpoint_name, limit, prefix_merger)
        params = Params(query_bundle.query.query)
        if params.has_params:
            params.set(params_dict)
            query = params.apply_parameters()
            query_bundle.query.query = query
        if with_stats:
            # Execute the query
            results, stats = query_bundle.get_lod_with_stats()
            self.store_stats([stats])
        else:
            results = query_bundle.get_lod()
            stats = None
        return results, stats

    def add_and_store(self, nq: NamedQuery):
        """
        Adds a new NamedQuery instance and stores it in the database.

        Args:
            nq (NamedQuery): The NamedQuery instance to add and store.

        """
        qd = QueryDetails.from_sparql(query_id=nq.query_id, sparql=nq.sparql)
        lod = []
        nq_record = asdict(nq)
        lod.append(nq_record)
        self.store(lod)
        qd_list = []
        qd_list.append(qd)
        self.store_query_details_list(qd_list)

    def get_entity_info(self, source_class: Type) -> EntityInfo:
        """
        Gets or creates EntityInfo for the given source class.
        """
        if source_class not in self.entity_infos:
            primary_key = self.primary_keys.get(source_class, None)
            sample_records = self.get_sample_records(source_class)
            self.entity_infos[source_class] = EntityInfo(
                sample_records,
                name=source_class.__name__,
                primaryKey=primary_key,
                debug=self.debug,
            )
        return self.entity_infos[source_class]

    def store(
        self,
        lod: List[Dict[str, Any]],
        source_class: Type = NamedQuery,
        with_create: bool = False,
    ) -> None:
        """
        Stores the given list of dictionaries in the database using entity information
        derived from a specified source class.

        Args:
            lod (List[Dict[str, Any]]): List of dictionaries that represent the records to be stored.
            source_class (Type): The class from which the entity information is derived. This class
                should have an attribute or method that defines its primary key and must have a `__name__` attribute.
                with_create(bool): if True create the table
        Raises:
            AttributeError: If the source class does not have the necessary method or attribute to define the primary key.
        """
        entity_info = self.get_entity_info(source_class)
        if with_create:
            self.sql_db.createTable4EntityInfo(entityInfo=entity_info, withDrop=True)
        # Store the list of dictionaries in the database using the defined entity information
        self.sql_db.store(lod, entity_info, fixNone=True, replace=True)

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
            raise AttributeError(
                f"The class {source_class.__name__} must have a 'get_samples' method."
            )

        sample_instances = source_class.get_samples()
        list_of_records = []

        # Assuming each key in the returned dictionary of get_samples corresponds to a list of instances
        for instance_group in sample_instances.values():
            for instance in instance_group:
                # Ensure that the instance is a dataclass instance
                if is_dataclass(instance):
                    record = asdict(instance)
                    list_of_records.append(record)
                else:
                    raise ValueError(
                        f"The instance of class {source_class.__name__} is not a dataclass instance"
                    )

        return list_of_records

    def lookup(self, query_name: QueryName, lenient: bool = True) -> NamedQuery:
        """
        lookup the named query for the given structured query name


        Args:
            query_name(QueryName): the structured query name
            lenient(bool): if True handle multiple entry errors as warnings
        Returns:
            NamedQuery: the named query
        """
        qn = query_name
        query_id = qn.query_id
        sql_query = """SELECT 
    *
FROM 
    NamedQuery 
WHERE 
    query_id=?"""
        query_records = self.sql_db.query(sql_query, (query_id,))
        if not query_records:
            msg = f"NamedQuery not found for the specified query '{qn}'."
            raise ValueError(msg)

        query_count = len(query_records)
        if query_count != 1:
            msg = f"multiple entries ({query_count}) for query '{qn.name}' namespace '{qn.namespace} and domain '{qn.domain}' the id '{qn.query_id}' is not unique"
            if lenient:
                print(f"warning: {msg}")
            else:
                raise ValueError(msg)

        record = query_records[0]
        named_query = NamedQuery.from_record(record)
        return named_query

    def get_query(
        self,
        query_name: QueryName,
        endpoint_name: str = "wikidata",
        limit: int = None,
        prefix_merger: QueryPrefixMerger = QueryPrefixMerger.SIMPLE_MERGER
    ) -> QueryBundle:
        """
        Get the query for the given parameters.

        Args:
            query_name: (QueryName):a structured query name
            endpoint_name (str): The name of the endpoint to send the SPARQL query to, default is 'wikidata'.
            limit (int): The query limit (if any).
            prefix_merger: Prefix merger to use
        Returns:
            QueryBundle: named_query, query, and endpoint.
        """
        named_query = self.lookup(query_name=query_name)
        return self.as_query_bundle(named_query, endpoint_name, limit, prefix_merger)

    def as_query_bundle(
        self, named_query: NamedQuery, endpoint_name: str, limit: int = None, prefix_merger: QueryPrefixMerger = QueryPrefixMerger.SIMPLE_MERGER
    ) -> QueryBundle:
        """
        Assembles a QueryBundle from a NamedQuery, endpoint name, and optional limit.

        Args:
            named_query (NamedQuery): Named query object.
            endpoint_name (str): Name of the endpoint where the query should be executed.
            limit (int): Optional limit for the query.

        Returns:
            QueryBundle: A bundle containing the named query, the query object, and the endpoint.
        """
        if endpoint_name not in self.endpoints:
            raise ValueError(f"Invalid endpoint {endpoint_name}")

        endpoint = self.endpoints[endpoint_name]
        query = Query(
            name=named_query.name,
            query=named_query.sparql,
            lang="sparql",
            endpoint=endpoint.endpoint,
            limit=limit,
        )
        query.query = QueryPrefixMerger.merge_prefixes(named_query, query, endpoint, prefix_merger)
        if limit:
            query.query += f"\nLIMIT {limit}"
        return QueryBundle(named_query=named_query, query=query, endpoint=endpoint)

    def get_namespaces(self) -> Dict[str, int]:
        """
        Retrieves all unique namespaces and the count of NamedQueries associated with each from the database,
        sorted by the count of queries from lowest to highest.

        Returns:
            Dict[str, int]: A dictionary where keys are namespaces and values are the counts of associated queries, sorted by count.
        """
        # Multi-line SQL query for better readability
        query = """
        SELECT domain,namespace, COUNT(*) AS query_count
        FROM NamedQuery
        GROUP BY domain,namespace
        ORDER BY COUNT(*)
        """
        result = self.sql_db.query(query)
        namespaces: Dict[str, int] = {}
        for row in result:
            domain = row["domain"]
            namespace = row["namespace"]
            count = int(row["query_count"])
            namespaces[f"{namespace}@{domain}"] = count
        return namespaces

    def get_all_queries(
        self,
        namespace: str = "snapquery-examples",
        domain: str = "wikidata.org",
        limit: int = None,  # Default limit is None, meaning no limit
    ) -> List[NamedQuery]:
        """
        Retrieves named queries stored in the database, filtered by domain and namespace with pattern matching.
        Optionally limits the number of results.

        Args:
            namespace (str): Namespace filter, supports wildcard '%', e.g., 'example%' for partial matches.
            domain (str): Domain filter, supports wildcard '%', e.g., 'wikidata%' for partial matches.
            limit (int): Maximum number of NamedQueries to retrieve, defaults to None for unlimited.

        Returns:
            List[NamedQuery]: A list of NamedQuery instances in the database.
        """
        sql_query = """SELECT * FROM NamedQuery 
WHERE domain LIKE ? AND namespace LIKE ?
ORDER BY domain,namespace,name"""
        params = (f"{domain}%", f"{namespace}%")

        if limit is not None:
            sql_query += " LIMIT ?"
            params += (limit,)

        query_records = self.sql_db.query(sql_query, params)
        named_queries = []
        for record in query_records:
            named_query = NamedQuery.from_record(record)
            named_queries.append(named_query)

        return named_queries

    def get_query_stats(self, query_id: str) -> list[QueryStats]:
        """
        Get query stats for the given query name
        Args:
            query_id: id of the query

        Returns:
            list of query stats
        """
        sql_query = """
        SELECT *
        FROM QueryStats
        WHERE query_id = ?
        """
        query_records = self.sql_db.query(sql_query, (query_id,))
        stats = []
        if query_records:
            for record in query_records:
                query_stat = QueryStats.from_record(record)
                stats.append(query_stat)
        return stats


class QueryNameSet:
    """
    Manages a set of QueryNames filtered by domain and namespaces SQL like patterns

    Attributes:

        nqm (NamedQueryManager): A manager to handle named queries and interactions with the database.
        limit(int): the maximum number of names and top_queries

    Calculated on update:
        total (int): Total number of queries that match the current filter criteria.
        domains (set): A set of domains that match the current filter criteria.
        namespaces (set): A set of namespaces that match the current filter criteria.
        names (set): A set of names that match the current filter criteria.
        top_queries (list): List of top queries based on the specified limit.
    """

    def __init__(self, nqm: "NamedQueryManager", limit: int = None):
        self.nqm = nqm
        self.limit = limit
        self.total = 0
        self.domains = set()
        self.namespaces = set()
        self.names = set()
        self.update("", "")

    def __str__(self):
        return (
            f"QueryNameSet(Total: {self.total}, Domains: {sorted(self.domains)}, "
            f"Namespaces: {sorted(self.namespaces)}, Names: {sorted(self.names)}, "
            f"Top Queries: [{', '.join(query.name for query in self.top_queries)}])"
        )

    def update(self, domain: str, namespace: str, limit: int = None):
        """
        update my attributes

        Args:
            domain (str): The domain part of the filter, supports SQL-like wildcards.
            namespace (str): The namespace part of the filter, supports SQL-like wildcards.
            limit (int, optional): Maximum number of queries to fetch. If None, no limit is applied.

        """
        if limit is None:
            limit = self.limit
        query = self.nqm.meta_qm.queriesByName["domain_namespace_stats"]
        params = (f"{domain}%", f"{namespace}%")
        results = self.nqm.sql_db.query(query.query, params)

        self.total = 0  # Reset total for each update call
        self.domains.clear()  # Clear previous domains
        self.namespaces.clear()  # Clear previous namespaces
        self.names.clear()  # Clear previous names

        for record in results:
            self.domains.add(record["domain"])
            self.namespaces.add(record["namespace"])
            self.total += record["query_count"]
        self.top_queries = self.nqm.get_all_queries(
            namespace=namespace, domain=domain, limit=limit
        )
        for query in self.top_queries:
            self.names.add(query.name)
