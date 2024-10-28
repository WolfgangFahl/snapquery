"""
Created on 2024-07-09

@author: wf
"""

import logging

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, QueryDetails, QueryPrefixMerger


class Execution:
    """
    supports execution of named queries
    """

    def __init__(self, nqm: NamedQueryManager, debug: bool = False):
        """ """
        self.nqm = nqm
        self.debug = debug
        self.logger = logging.getLogger("snapquery.execution.Execution")

    def parameterize(self, nq: NamedQuery):
        """
        parameterize the given named query
        see
        https://github.com/WolfgangFahl/snapquery/issues/33
        """
        qd = QueryDetails.from_sparql(query_id=nq.query_id, sparql=nq.sparql)
        # Execute the query
        params_dict = {}
        # @FIXME - you can't do this - hard code
        # the parameter out of blue air
        if qd.params == "q":
            # use Tim Berners-Lee as a example
            params_dict = {"q": "Q80"}
            pass
        return qd, params_dict

    def execute(
        self,
        nq: NamedQuery,
        endpoint_name: str,
        title: str,
        context: str = "test",
        prefix_merger: QueryPrefixMerger = QueryPrefixMerger.SIMPLE_MERGER,
    ):
        """
        execute the given named query
        """
        qd, params_dict = self.parameterize(nq)
        self.logger.debug(f"{title}: {nq.name} {qd} - via {endpoint_name}")
        _results, stats = self.nqm.execute_query(
            nq, params_dict=params_dict, endpoint_name=endpoint_name, prefix_merger=prefix_merger
        )
        stats.context = context
        self.nqm.store_stats([stats])
        msg = f"{title} executed:"
        if not stats.records:
            msg += f"error {stats.filtered_msg}"
        else:
            msg += f"{stats.records} records found"
        self.logger.debug(msg)
