"""
Created on 2024-05-03

@author: wf
"""

import asyncio
from typing import List

from lodstorage.query import QuerySyntaxHighlight, ValueFormatter
from ngwidgets.dict_edit import DictEdit
from ngwidgets.input_webserver import InputWebSolution
from ngwidgets.lod_grid import ListOfDictsGrid
from ngwidgets.widgets import Link
from nicegui import background_tasks, run, ui

from snapquery.error_filter import ErrorFilter
from snapquery.params import Params
from snapquery.snapquery_core import NamedQuery, QueryBundle, QueryStats


class NamedQueryView:
    """
    display a named Query
    """

    def __init__(
        self,
        solution: InputWebSolution,
        query_bundle: QueryBundle,
        r_format_str: str = "html",
    ):
        self.solution = solution
        self.nqm = self.solution.nqm
        self.query_bundle = query_bundle
        self.r_format_str = r_format_str
        self.load_task = None
        self.limit = 200
        self.timeout = 20.0
        # preload ValueFormatter
        ValueFormatter.getFormats()
        self.setup_ui()

    def setup_ui(self):
        """
        setup my user interface
        """
        nq = self.query_bundle.named_query
        url = self.query_bundle.query.tryItUrl
        text = nq.title
        tooltip = "try it!"
        link = Link.create(url, text, tooltip, target="_blank")
        with self.solution.container:
            with ui.row() as self.query_settings_row:
                ui.number(label="limit").bind_value(self, "limit")
                ui.number(label="time out").bind_value(self, "timeout")
            with ui.row() as self.query_row:
                self.try_it_link = ui.html(link)
                ui.label(nq.description)
                self.params = Params(nq.sparql)
                if self.params.has_params:
                    self.params_edit = self.params.get_dict_edit()
                    pass
                ui.button(icon="play_arrow", on_click=self.run_query)
                self.stats_html = ui.html()
            with ui.row():
                with ui.expansion("Show Query", icon="manage_search").classes("w-full"):
                    query_syntax_highlight = QuerySyntaxHighlight(
                        self.query_bundle.query
                    )
                    syntax_highlight_css = (
                        query_syntax_highlight.formatter.get_style_defs()
                    )
                    ui.add_css(syntax_highlight_css)
                    ui.html(query_syntax_highlight.highlight())
            self.grid_row = ui.row()
            pass

    async def load_query_results(self):
        """
        (re) load the query results
        """
        if self.params.has_params:
            self.query_bundle.query.query = self.params.apply_parameters()
            self.params.close()
        self.query_bundle.set_limit(int(self.limit))
        (lod, stats) = await run.io_bound(self.query_bundle.get_lod_with_stats)
        self.nqm.store(
            [stats.as_record()], source_class=QueryStats, primary_key="stats_id"
        )
        self.grid_row.clear()
        if stats.error_msg:
            with self.grid_row:
                error_filter = ErrorFilter(stats.error_msg)
                filtered_msg = error_filter.get_message()
                markup = f'<span style="color: red;">{filtered_msg}</span>'
                ui.html(markup)
        else:
            with self.query_row:
                record_count = len(lod) if lod is not None else 0
                markup = f'<span style="color: green;">{record_count} records in {stats.duration:.2f} secs</span>'
                self.stats_html.content = markup
        if not lod:
            with self.query_row:
                ui.notify("query failed")
            return
        query = self.query_bundle.query
        query.formats = ["*:wikidata"]
        tablefmt = "html"
        query.preFormatWithCallBacks(lod, tablefmt=tablefmt)
        query.formatWithValueFormatters(lod, tablefmt=tablefmt)
        for record in lod:
            for key, value in record.items():
                if isinstance(value, str):
                    if value.startswith("http"):
                        record[key] = Link.create(value, value)
        with self.grid_row:
            self.lod_grid = ListOfDictsGrid()
            self.lod_grid.load_lod(lod)
        self.grid_row.update()

    async def run_query(self, _args):
        """
        run the current query
        """

        def cancel_running():
            if self.load_task:
                self.load_task.cancel()

        self.grid_row.clear()
        with self.grid_row:
            ui.spinner()
        self.grid_row.update()
        # cancel task still running
        cancel_running()
        # cancel task if it takes too long
        ui.timer(self.timeout, lambda: cancel_running(), once=True)
        # run task in background
        self.load_task = background_tasks.create(self.load_query_results())


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
        self.namespace = ""
        self.name = ""

    def setup_ui(self):
        """
        setup my user interface
        """
        with ui.row() as self.search_row:
            self.name_search_input = (
                ui.input(label="name", on_change=self.on_search_change)
                .bind_value(self, "name")
                .props("size=80")
            )
            self.namespace_search_input = (
                ui.input(label="namespace", on_change=self.on_search_change)
                .bind_value(self, "namespace")
                .props("size=40")
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
