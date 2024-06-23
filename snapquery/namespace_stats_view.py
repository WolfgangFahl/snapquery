'''
Created on 2024-06-23

@author: wf
'''
from nicegui import ui, run
from snapquery.snapquery_core import NamedQueryManager, NamedQuery, QueryStats
from ngwidgets.lod_grid import ListOfDictsGrid, GridConfig
from ngwidgets.webserver import WebSolution

class NamespaceStatsView:
    """Class to view and manage SPARQL query statistics using NiceGUI."""

    def __init__(self,solution:WebSolution):
        self.solution=solution
        self.nqm = self.solution.nqm
        self.setup_ui()

    def setup_ui(self):
        """Sets up the user interface for displaying 
        SPARQL query statistics."""
        with ui.row() as self.results_row:
            self.lod_grid=ListOfDictsGrid()
        ui.timer(0.0, self.on_fetch_lod, once=True)
        
    async def on_fetch_lod(self, _args=None):
        try:
            stats_lod=await run.io_bound(self.fetch_query_lod)
            with self.results_row:
                self.lod_grid.load_lod(stats_lod)
                self.lod_grid.update()
        except Exception as ex:
            self.solution.handle_exception(ex)
            
    def fetch_query_lod(self):
        query_name = 'query_success_by_namespace'
        query = self.nqm.meta_qm.queriesByName[query_name]
        return self.nqm.sql_db.query(query.query)