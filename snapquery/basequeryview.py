"""
Created on 2024-06-23

@author: wf
"""
import asyncio
from nicegui import ui
from ngwidgets.webserver import WebSolution
from ngwidgets.lod_grid import ListOfDictsGrid
from snapquery.snapquery_core import NamedQuery
from snapquery.query_selector import QuerySelector
from typing import List

class BaseQueryView:
    """
    general search for queries
    """
    def __init__(self, solution: WebSolution):
        self.solution = solution
        self.nqm = self.solution.nqm
        self.search_debounce_task = None
        self.keystroke_time = 0.65  # minimum time in seconds to wait between keystrokes before starting searching
        self.setup_ui()
        self.namespace = ""
        self.name = ""

    def setup_ui(self):
        """
        setup my user interface
        """
        with ui.row().classes("w-full"):
            with ui.column().classes("w-full"):
                ui.label("Available Queries").classes("text-xl")
                ui.label("select a query to view and execute").classes("text-slate-400")

        with ui.row() as self.select_row:
            self.query_selector=QuerySelector(self.solution)

        with ui.row() as self.search_row:
            self.domain_search_input = (
                ui.input(label="domain", on_change=self.on_search_change)
                .bind_value(self, "domain")
                .props("size=40")
            )
            self.namespace_search_input = (
                ui.input(label="namespace", on_change=self.on_search_change)
                .bind_value(self, "namespace")
                .props("size=40")
            )
            self.name_search_input = (
                ui.input(label="name", on_change=self.on_search_change)
                .bind_value(self, "name")
                .props("size=80")
            )
        self.search_result_row = ui.row()
        ui.timer(0.0, self.on_search_change, once=True)

    async def on_search_change(self, _args=None):
        """
        react on changes in the search input
        """
        # Cancel the existing search task if it's still waiting
        if self.search_debounce_task:
            self.search_debounce_task.cancel()

        # Create a new task for the new search
        self.search_debounce_task = asyncio.create_task(self.debounced_search())

    async def debounced_search(self):
        """
        Waits for a period of inactivity and then performs the search.
        """
        try:
            # Wait for the debounce period (keystroke_time)
            await asyncio.sleep(self.keystroke_time)
            sql_query = """SELECT 
* 
FROM NamedQuery 
WHERE name LIKE ? and namespace LIKE? AND domain like?"""
            name_like = f"{self.name}%"
            namespace_like = f"{self.namespace}%"
            domain_like = f"{self.domain}%"
            self.q_lod = self.nqm.sql_db.query(sql_query, (name_like, namespace_like, domain_like))
            self.show_lod(self.q_lod)

        except asyncio.CancelledError:
            # The search was cancelled because of new input, so just quietly exit
            pass
        except Exception as ex:
            self.solution.handle_exception(ex)

    def show_lod(self, q_lod: List):
        """
        show the given list of dicts
        """
        self.search_result_row.clear()
        view_lod = []
        for record in self.q_lod:
            nq = NamedQuery.from_record(record)
            vr = nq.as_viewrecord()
            view_lod.append(vr)
        with self.search_result_row:
            self.search_result_grid = ListOfDictsGrid()
            ui.notify(f"found {len(q_lod)} queries")
            self.search_result_grid.load_lod(view_lod)
        self.search_result_row.update()

