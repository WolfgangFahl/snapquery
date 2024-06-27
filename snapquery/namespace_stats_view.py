"""
Created on 2024-06-23

@author: wf
"""

import logging
from collections import defaultdict
from typing import Dict, List, Optional
from ngwidgets.progress import NiceguiProgressbar
from ngwidgets.lod_grid import GridConfig, ListOfDictsGrid
from ngwidgets.webserver import WebSolution
from nicegui import run, ui

from snapquery.snapquery_core import NamedQuery, QueryDetails

logger = logging.getLogger(__name__)


class NamespaceStatsView:
    """Class to view and manage SPARQL query statistics using NiceGUI.

    Attributes:
        solution (WebSolution): The web solution context which provides access to shared resources.
        nqm (NamedQueryManager): The manager to handle named queries and database interactions.
        results_row (ui.row): UI component that holds the results grid.
        lod_grid (ListOfDictsGrid): Grid component to display the query statistics.
    """

    def __init__(self, solution: WebSolution):
        """Initialize the NamespaceStatsView with a given web solution context.

        Args:
            solution (WebSolution): The web solution context which includes shared resources like the NamedQueryManager.
        """
        self.solution = solution
        self.nqm = self.solution.nqm
        self.progress_bar: Optional[NiceguiProgressbar] = None
        self.lod_grid: Optional[ListOfDictsGrid] = None
        self.setup_ui()

    def setup_ui(self):
        """Sets up the user interface for displaying SPARQL query statistics."""
        with ui.row() as self.progress_row:
            self.progress_bar = NiceguiProgressbar(
                desc="Query Progress", total=100, unit="queries"
            )
        with ui.row() as self.results_row:
            self.lod_grid = ListOfDictsGrid()
            # Set up a click event handler for the grid
            self.lod_grid.ag_grid.on("cellClicked", self.on_cell_clicked)

        # Fetch and display data immediately upon UI setup
        ui.timer(0.0, self.on_fetch_lod, once=True)

    def execute(self, nq: NamedQuery, endpoint_name: str, title: str):
        """Execute the given named query with notification and progress bar updates."""
        qd, params_dict = self.parameterize(nq)
        with self.results_row:
            msg = f"{title}: {nq.name} {qd} - via {endpoint_name}"
            logger.info(msg)
            # ui.notify(msg)

        results, stats = self.nqm.execute_query(nq, params_dict, endpoint_name)
        stats.context = "test"
        self.nqm.store_stats([stats])

        with self.results_row:
            if not stats.records:
                msg = f"{title} error: {stats.filtered_msg}"
                logger.error(msg)
            else:
                msg = f"{title} executed: {stats.records} records found"
                logger.info(msg)
                # ui.notify(msg, kind="success")

    def execute_queries(self, namespace: str, endpoint_name: str):
        """execute queries with progress updates.

        Args:
            namespace (str): The namespace of the queries to execute.
            endpoint_name (str): The endpoint name where the queries will be executed.
        """
        queries = self.nqm.get_all_queries(namespace=namespace)
        total_queries = len(queries)
        count = 0

        self.progress_bar.total = total_queries
        self.progress_bar.reset()

        for i, nq in enumerate(queries, start=1):
            count += 1
            with self.progress_row:
                self.progress_bar.update_value(count)
                self.progress_bar.set_description(
                    f"Executing {nq.name} on {endpoint_name}"
                )
                logger.debug(f"Executing {nq.name} on {endpoint_name}")
                self.progress_row.update()
            self.execute(
                nq, endpoint_name, title=f"query {i}/{len(queries)}::{endpoint_name}"
            )
            with self.progress_row:
                self.progress_bar.set_description(
                    f"Completed {count} of {total_queries} queries"
                )

    async def on_cell_clicked(self, event):
        """Handle cell click events to perform specific actions based on the cell content."""
        # Retrieve details from the event object
        logger.debug(f"Cell clicked: {event}")
        row_data = event.args["data"]
        endpoint_name = event.args["colId"]
        namespace = row_data["namespace"]
        if endpoint_name in self.nqm.endpoints.keys():
            await run.io_bound(
                self.execute_queries, namespace=namespace, endpoint_name=endpoint_name
            )

    async def on_fetch_lod(self, _args=None):
        """Fetches data asynchronously and loads it into the grid upon successful retrieval."""
        try:
            stats_lod = await run.io_bound(self.fetch_query_lod)
            processed_lod = self.process_stats_lod(stats_lod)
            with self.results_row:
                self.lod_grid.load_lod(processed_lod)
                self.lod_grid.update()
        except Exception as ex:
            self.solution.handle_exception(ex)

    def fetch_query_lod(self) -> List[Dict[str, any]]:
        """Fetch data from the database based on the named query 'query_success_by_namespace'.

        Returns:
            List[Dict[str, any]]: A list of dictionaries containing the query results.
        """
        query_name = "query_namespace_endpoint_matrix_with_distinct"
        query = self.nqm.meta_qm.queriesByName[query_name]
        return self.nqm.sql_db.query(query.query)

    def process_stats_lod(self, raw_lod: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Process the raw list of dictionaries to format suitable for the grid display.

        Args:
            raw_lod (List[Dict[str, any]]): The raw data fetched from the SQL query.

        Returns:
            List[Dict[str, any]]: The processed list of dictionaries formatted for grid display.
        """
        namespace_stats = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
        endpoints = list(self.nqm.endpoints.keys())
        total_queries = {}

        for entry in raw_lod:
            namespace = entry["namespace"]
            endpoint = entry["endpoint_name"]
            distinct_successful = entry.get("distinct_successful", 0)
            distinct_failed = entry.get("distinct_failed", 0)
            success_count = entry["success_count"]
            total_queries[namespace] = entry["total"]
            namespace_stats[namespace][endpoint] = [distinct_successful, distinct_failed, success_count]

        processed_lod = []
        for namespace, counts in namespace_stats.items():
            row = {"namespace": namespace, "total": total_queries[namespace]}
            for endpoint in endpoints:
                stats = counts.get(endpoint, [0, 0, 0])
                row[endpoint] = f"✅{stats[0]} ❌{stats[1]} 🔄{stats[2]}"
            processed_lod.append(row)

        return processed_lod

    def parameterize(self, nq: NamedQuery):
        """
        parameterize the given named query
        ToDo: Find a better way to parameterize the given named query currently this function is used in snapquery_cmd.py, test_query_execution.py, and here

        Args:
            nq(NamedQuery): the query to parameterize
        """
        qd = QueryDetails.from_sparql(query_id=nq.query_id, sparql=nq.sparql)
        # Execute the query
        params_dict = {}
        if qd.params == "q":
            # use Tim Berners-Lee as a example
            params_dict = {"q": "Q80"}
            pass
        return qd, params_dict
