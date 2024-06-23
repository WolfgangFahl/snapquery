"""
Created on 2024-06-23

@author: wf
"""
from collections import defaultdict
from typing import Dict, List

from ngwidgets.lod_grid import GridConfig, ListOfDictsGrid
from ngwidgets.webserver import WebSolution
from nicegui import run, ui

from snapquery.snapquery_core import NamedQueryManager


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
        self.setup_ui()

    def setup_ui(self):
        """Sets up the user interface for displaying SPARQL query statistics."""
        with ui.row() as self.results_row:
            self.lod_grid = ListOfDictsGrid()

        # Fetch and display data immediately upon UI setup
        ui.timer(0.0, self.on_fetch_lod, once=True)

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
        query_name = "query_namespace_endpoint_matrix"
        query = self.nqm.meta_qm.queriesByName[query_name]
        return self.nqm.sql_db.query(query.query)

    def process_stats_lod(self, raw_lod: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """Process the raw list of dictionaries to format suitable for the grid display.

        Args:
            raw_lod (List[Dict[str, any]]): The raw data fetched from the SQL query.

        Returns:
            List[Dict[str, any]]: The processed list of dictionaries formatted for grid display.
        """
        namespace_stats = defaultdict(lambda: defaultdict(int))
        endpoints = list(
            self.nqm.endpoints.keys()
        )  # Get all endpoint names from the NamedQueryManager

        # Aggregate counts by namespace and endpoint
        for entry in raw_lod:
            namespace = entry["namespace"]
            endpoint = entry["endpoint_name"]
            count = entry["success_count"]
            namespace_stats[namespace][endpoint] += count

        # Convert aggregated data to list of dicts format for the grid
        processed_lod = []
        for namespace, counts in namespace_stats.items():
            row = {"namespace": namespace}
            total = 0
            for endpoint in endpoints:
                row[endpoint] = counts.get(endpoint, 0)
                total += row[endpoint]
            row["total"] = total
            processed_lod.append(row)

        return processed_lod
