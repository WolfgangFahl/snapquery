"""
Created on 2024-05-03

@author: wf
"""
import asyncio
from typing import List

from ngwidgets.input_webserver import InputWebSolution
from ngwidgets.lod_grid import ListOfDictsGrid
from nicegui import ui

from snapquery.snapquery_core import NamedQuery


class NamedQuerySearch:
    """
    search for namedqueries
    """

    def __init__(self, solution: InputWebSolution):
        self.solution = solution
        self.nqm = self.solution.nqm
        self.search_debounce_task = None
        self.keystroke_time = 0.65  # minimum time in seconds to wait between keystrokes before starting searching
        self.setup_ui()
        self.namespace = "wikidata-examples"
        self.name = ""

    def setup_ui(self):
        """
        setup my user interface
        """
        with ui.row() as self.search_row:
            self.namespace_search_input = (
                ui.input(label="namespace", on_change=self.on_search_change)
                .bind_value(self, "namespace")
                .props("size=80")
            )
            self.name_search_input = (
                ui.input(label="name", on_change=self.on_search_change)
                .bind_value(self, "name")
                .props("size=80")
            )
        with ui.row() as self.search_result_row:
            self.search_result_grid = ListOfDictsGrid()

    async def on_search_change(self, _args):
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
WHERE name LIKE ? and namespace LIKE? """
            name_like = f"{self.name}%"
            namespace_like = f"{self.namespace}%"
            self.q_lod = self.nqm.sql_db.query(sql_query, (name_like, namespace_like))
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
        view_lod = []
        for record in self.q_lod:
            nq = NamedQuery.from_record(record)
            vr = nq.as_viewrecord()
            view_lod.append(vr)
        if self.search_result_row:
            with self.search_result_row:
                ui.notify(f"found {len(q_lod)} queries")
                self.search_result_grid.load_lod(view_lod)
                # self.search_result_grid.set_checkbox_selection("#")
                self.search_result_grid.update()
