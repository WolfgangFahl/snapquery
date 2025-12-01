"""
Created on 2024-05-03

@author: wf
"""

import pandas as pd
import plotly.express as px
from lodstorage.params import Params
from lodstorage.query import QuerySyntaxHighlight, ValueFormatter, ValueFormatters
from ngwidgets.input_webserver import InputWebSolution
from ngwidgets.lod_grid import ListOfDictsGrid
from ngwidgets.widgets import Link
from nicegui import background_tasks, run, ui

from snapquery.basequeryview import BaseQueryView
from snapquery.params_view import ParamsView
from snapquery.query_annotate import SparqlQueryAnnotater
from snapquery.snapquery_core import NamedQueryManager, QueryBundle, QueryStats


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
        self.endpoint_name = "wikidata"
        self.nqm: NamedQueryManager = self.solution.nqm
        self.query_bundle = query_bundle
        self.r_format_str = r_format_str
        self.load_task = None
        self.limit = 200
        self.timeout = 20.0
        # preload ValueFormatters
        ValueFormatters.get_instance()
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
            with ui.column():
                with ui.row() as self.query_settings_row:
                    self.query_settings_row.classes("w-full")
                    ui.number(label="limit").bind_value(self, "limit")
                    ui.number(label="time out").bind_value(self, "timeout")
                    endpoint_selector = ui.select(
                        list(self.nqm.endpoints.keys()),
                        value=self.solution.endpoint_name,
                        label="endpoint",
                    )
                    endpoint_selector.bind_value(
                        self,
                        "endpoint_name",
                    )
                    endpoint_selector.classes("w-64")
                with ui.row() as self.query_row:
                    self.try_it_link = ui.html(link)
                    ui.label(nq.description)
                    self.params = Params(nq.sparql)
                    if self.params.has_params:
                        self.params_view = ParamsView(self, self.params)
                        self.params_edit = self.params_view.get_dict_edit()
                        pass
                    ui.button(icon="play_arrow", on_click=self.run_query)
                    self.stats_html = ui.html()
                with ui.row():
                    with ui.expansion("Show Query", icon="manage_search").classes("w-full"):
                        query_syntax_highlight = QuerySyntaxHighlight(self.query_bundle.query)
                        syntax_highlight_css = query_syntax_highlight.formatter.get_style_defs()
                        annotated_query = SparqlQueryAnnotater(self.query_bundle.query)
                        ui.add_css(syntax_highlight_css)
                        # ui.html(query_syntax_highlight.highlight())
                        ui.html(annotated_query.annotate())
                if self.solution.webserver.authenticated():
                    with ui.row().classes("w-full"):
                        with ui.expansion("Show Query Stats", icon="query_stats") as self.stats_container:
                            self.stats_container.classes("w-full")
                            self.load_stats()
                self.grid_row = ui.expansion("Query Results", icon="table_rows", value=True)
                self.grid_row.classes("w-full")
                with self.grid_row:
                    ui.label("Not yet executed ")
                    ui.button("Run Query", icon="play_arrow", on_click=self.run_query)
                pass

    def load_stats(self):
        """
        display query stats
        """
        self.stats_container.clear()
        with self.stats_container:
            container = ui.row()
        query_stats = self.nqm.get_query_stats(self.query_bundle.named_query.query_id)
        errors = [stat for stat in query_stats if not stat.is_successful()]
        successful = [stat for stat in query_stats if stat.is_successful()]
        if successful:
            exec_times_by_endpoint: dict[str, list[QueryStats]] = {}
            for stat in successful:
                if stat.endpoint_name not in exec_times_by_endpoint:
                    exec_times_by_endpoint[stat.endpoint_name] = []
                exec_times_by_endpoint[stat.endpoint_name].append(stat)
            data = []
            for endpoint_name, stats in exec_times_by_endpoint.items():
                record = {
                    "type": "box",
                    "name": endpoint_name,
                    "x": [stat.duration for stat in stats],
                }
                data.append(record)
            fig = {
                "data": data,
                "layout": {
                    "margin": {"l": 200, "r": 15, "t": 30, "b": 30},
                    "plot_bgcolor": "#E5ECF6",
                    "xaxis": {"gridcolor": "white", "title": "Execution Time [s]"},
                    "yaxis": {"gridcolor": "white", "title": "Endpoint"},
                    "title": "Query Execution Times by Endpoint",
                },
                "config": {
                    "staticPlot": True,
                },
            }
            with container:
                ui.plotly(fig)
        if errors:
            error_records = [stat.as_record() for stat in errors]
            for record in error_records:
                if record["error_msg"]:
                    record["error_msg"] = record["error_msg"][:16] + "..."
                else:
                    record["error_msg"] = "<unkown>"
            error_df = pd.DataFrame.from_records(error_records)
            error_df_grouped = error_df.groupby(["endpoint_name", "error_msg"], as_index=False).count()
            error_fig = px.bar(
                error_df_grouped,
                x="endpoint_name",
                y="query_id",
                title="Query Execution Errors",
                labels={"query_id": "count", "endpoint_name": "Endpoint"},
                color="error_msg",
            )
            error_fig.update_layout(margin=dict(l=15, r=15, t=30, b=15))
            with container:
                ui.plotly(error_fig)
        if not successful and not errors:
            with container:
                ui.label("No query statistics available")
        with container:
            ui.button("Update statistics", icon="update", on_click=self.load_stats)

    async def load_query_results(self):
        """
        (re) load the query results
        """
        if self.params.has_params:
            self.query_bundle.query.query = self.params.apply_parameters()
            self.params_view.close()
        self.query_bundle.set_limit(int(self.limit))
        endpoint = self.nqm.endpoints[self.endpoint_name]
        self.query_bundle.update_endpoint(endpoint)
        result = await run.io_bound(self.query_bundle.get_lod_with_stats)
        if not result:
            with self.solution.container:
                ui.notify("query execution failure")
            return
        lod, stats = result
        self.nqm.store_stats([stats])
        self.grid_row.clear()
        if stats.error_msg:
            with self.grid_row:
                stats.apply_error_filter()
                markup = f'<span style="color: red;">{stats.filtered_msg}</span>'
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


class NamedQuerySearch(BaseQueryView):
    """
    search for namedqueries
    """

    def __init__(self, solution: InputWebSolution):
        super().__init__(solution)
