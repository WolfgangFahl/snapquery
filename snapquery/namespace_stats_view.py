"""
Created on 2024-06-23

@author: wf
"""

import logging
from collections import defaultdict
from typing import Dict, List, Optional

from ngwidgets.lod_grid import GridConfig, ListOfDictsGrid
from ngwidgets.progress import NiceguiProgressbar
from ngwidgets.webserver import WebSolution
from nicegui import run, ui
from snapquery.execution import Execution
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
            self.progress_bar = NiceguiProgressbar(desc="Query Progress", total=100, unit="queries")
            self.progress_bar.progress.classes("rounded")
        with ui.row() as self.results_row:
            ui.label("Legend: ✅ Distinct Successful Queries  ❌ Distinct Failed Queries  🔄 Total Successful Runs")
            self.lod_grid = ListOfDictsGrid()
            # Set up a click event handler for the grid
            self.lod_grid.ag_grid.on("cellClicked", self.on_cell_clicked)

        # Fetch and display data immediately upon UI setup
        ui.timer(0.0, self.on_fetch_lod, once=True)

    async def on_cell_clicked(self, event):
        """Handle cell click events to perform specific actions based on the cell content."""
        # Retrieve details from the event object
        logger.debug(f"Cell clicked: {event}")
        row_data = event.args["data"]
        endpoint_name = event.args["colId"]
        namespace = row_data["namespace"]
        domain = row_data["domain"]
        if endpoint_name in self.nqm.endpoints.keys():
            if self.solution.webserver.authenticated():
                await run.io_bound(
                    self.execute_queries,
                    namespace=namespace,
                    endpoint_name=endpoint_name,
                    domain=domain,
                )
            else:
                ui.notify("you must be admin to run queries via the web interface")
        else:
            # this should not be possible
            ui.notify(f"invalid endpoint {endpoint_name}")

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
        domain_namespace_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: [0, 0, 0])))
        endpoints = list(self.nqm.endpoints.keys())
        total_queries = {}

        for entry in raw_lod:
            domain = entry["domain"]
            namespace = entry["namespace"]
            endpoint = entry["endpoint_name"]
            distinct_successful = entry.get("distinct_successful", 0)
            distinct_failed = entry.get("distinct_failed", 0)
            success_count = entry["success_count"]
            total_queries[(domain, namespace)] = entry["total"]
            domain_namespace_stats[domain][namespace][endpoint] = [
                distinct_successful,
                distinct_failed,
                success_count,
            ]

        processed_lod = []
        for domain, namespaces in domain_namespace_stats.items():
            for namespace, counts in namespaces.items():
                row = {
                    "domain": domain,
                    "namespace": namespace,
                    "total": total_queries[(domain, namespace)],
                }
                for endpoint in endpoints:
                    success, fail, total = counts.get(endpoint, [0, 0, 0])
                    if success == 0 and fail == 0 and total == 0:
                        row[endpoint] = ""
                    else:
                        row[endpoint] = f"✅{success} ❌{fail} 🔄{total}"
                processed_lod.append(row)

        return processed_lod

    def execute_queries(self, namespace: str, endpoint_name: str, domain: str):
        """execute queries with progress updates.
        Args:
            namespace (str): The namespace of the queries to execute.
            endpoint_name (str): The endpoint name where the queries will be executed.
            domain: domain name
        """
        queries = self.nqm.get_all_queries(namespace=namespace, domain=domain)
        total_queries = len(queries)

        self.progress_bar.total = total_queries
        self.progress_bar.reset()
        execution=Execution(self.nqm)
        for i, nq in enumerate(queries, start=1):
            with self.progress_row:
                self.progress_bar.update_value(i)
                self.progress_bar.set_description(f"Executing {nq.name} on {endpoint_name}")
                logger.debug(f"Executing {nq.name} on {endpoint_name}")
            execution.execute(
                nq,
                endpoint_name,
                title=f"query {i}/{len(queries)}::{endpoint_name}",
                context="web-test"
            )
        with self.progress_row:
            ui.timer(0.1, self.on_fetch_lod, once=True)
            ui.notify(
                f"finished {total_queries} queries for namespace: {namespace} with domain: {domain}",
                type="positive",
            )