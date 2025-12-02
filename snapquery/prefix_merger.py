"""
Created 2024

@author: tholzheim

Move to separate module in 2025-12-01 by wf
"""

import logging
from enum import Enum

from lodstorage.prefix_config import PrefixConfigs
from lodstorage.prefixes import Prefixes
from lodstorage.query import Endpoint, Query

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
        logging.warning(f"Invalid QueryPrefixMerger key: {key}, defaulting to SIMPLE_MERGER")
        merger = cls.default_merger()
        return merger

    @classmethod
    def default_merger(cls) -> "QueryPrefixMerger":
        merger = cls.SIMPLE_MERGER
        return merger

    @classmethod
    def get_by_name(cls, name: str) -> "QueryPrefixMerger":
        merger_map = {merger.name: merger.value for merger in QueryPrefixMerger}
        merger_value = merger_map.get(name, None)
        merger = QueryPrefixMerger(merger_value)
        return merger

    @classmethod
    def merge_prefixes(
        cls,
        query: Query,
        endpoint: Endpoint,
        merger: "QueryPrefixMerger",
    ) -> str:
        """
        Merge prefixes with the given merger
        Args:
            query (Query):
            endpoint (Endpoint):
            merger (QueryPrefixMerger):

        Returns:
            merged query
        """
        sparql_query = query.query
        if merger == QueryPrefixMerger.SIMPLE_MERGER:
            sparql_query = cls.simple_prefix_merger(sparql_query, endpoint)
        elif merger == QueryPrefixMerger.ANALYSIS_MERGER:
            sparql_query = cls.analysis_prefix_merger(sparql_query)
        return sparql_query

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
        prefixes_str = endpoint.get_prefixes(PrefixConfigs.get_instance())
        if not prefixes_str.strip():
            return

        merged_query = Prefixes.merge_prefixes(query_str, prefixes_str)
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
