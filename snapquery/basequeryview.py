"""
Created on 2024-06-23
@author: wf
"""

from typing import List

from ngwidgets.debouncer import DebouncerUI
from ngwidgets.lod_grid import ListOfDictsGrid
from ngwidgets.webserver import WebSolution
from nicegui import ui

from snapquery.query_selector import QuerySelector
from snapquery.snapquery_core import NamedQuery


class BaseQueryView:
    """
    general search for queries
    """

    def __init__(self, solution: WebSolution, debug: bool = False):
        self.solution = solution
        self.nqm = self.solution.nqm
        self.debug = debug
        self.setup_ui()

    def setup_ui(self):
        """
        setup my user interface
        """
        with ui.row().classes("w-full items-baseline") as self.header_row:
            ui.label("Available Queries").classes("text-xl")
            ui.label("select a query to view and execute").classes("text-slate-400")

        self.query_selector = QuerySelector(self.solution, self.on_search_change)
        self.search_result_row = ui.row()
        self.debouncer = DebouncerUI(parent=self.search_result_row, delay=0.65, debug=self.debug)

        ui.timer(0.0, self.on_search_change, once=True)

    async def on_search_change(self, _args=None):
        """
        react on changes in the search input
        """
        await self.debouncer.debounce(self.perform_search)

    async def perform_search(self):
        """
        Performs the search based on the current
        QuerySelector values qn (query_name) and like (LIKE or =) comparison

        """
        try:
            qn = self.query_selector.qn
            like = self.query_selector.like

            if like:
                name_pattern = f"{qn.name}%"
                namespace_pattern = f"{qn.namespace}%"
                domain_pattern = f"{qn.domain}%"
                comparison_operator = "LIKE"
            else:
                name_pattern = qn.name
                namespace_pattern = qn.namespace
                domain_pattern = qn.domain
                comparison_operator = "="

            sql_query = f"""SELECT
                *
                FROM NamedQuery
                WHERE
                name {comparison_operator} ?
                AND namespace {comparison_operator} ?
                AND domain {comparison_operator} ?"""

            self.q_lod = self.nqm.sql_db.query(sql_query, (name_pattern, namespace_pattern, domain_pattern))
            self.show_lod(self.q_lod)
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
