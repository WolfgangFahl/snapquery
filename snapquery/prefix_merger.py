"""
Created 2024

@author: tholzheim

Move to separate module in 2025-12-01 by wf
"""
from enum import Enum

from lodstorage.query import Query, Endpoint
from snapquery.snapquery_core import NamedQuery
from snapquery.sparql_analyzer import SparqlAnalyzer


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
    def get_by_name(cls, name: str) -> "QueryPrefixMerger":
        merger_map = {merger.name: merger.value for merger in QueryPrefixMerger}
        merger_value = merger_map.get(name, None)
        merger = QueryPrefixMerger(merger_value)
        return merger

    @classmethod
    def merge_prefixes(
        cls,
        named_query: NamedQuery,
        query: Query,
        endpoint: Endpoint,
        merger: "QueryPrefixMerger",
    ) -> str:
        """
        Merge prefixes with the given merger
        Args:
            named_query (NamedQuery):
            query (Query):
            endpoint (Endpoint):
            merger (QueryPrefixMerger):

        Returns:
            merged query
        """
        if merger == QueryPrefixMerger.SIMPLE_MERGER:
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
            query_str (str): the query string
            endpoint (Endpoint): the endpoint

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