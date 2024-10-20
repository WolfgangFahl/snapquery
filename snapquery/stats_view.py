import plotly.express as px
from nicegui import ui
from pandas import DataFrame

from snapquery.query_annotate import QUERY_ITEM_STATS


class QueryStatsView:
    """
    display Query Import UI
    """

    def __init__(self, solution=None):
        self.solution = solution
        if self.solution:
            self.nqm = self.solution.nqm
            self.setup_ui()

    def setup_ui(self):
        """
        setup the user interface
        """
        with self.solution.container:
            with ui.expansion(
                text="Statistics about the properties and items used in the stored queries",
                value=True,
            ):
                self.input_row = ui.column()
                self.input_row.classes("w-full")
                self.show_entity_usage()
                self.show_property_usage()
                self.show_keyword_usage()
                self.show_function_usage()
                self.show_namespace_usage()
            with ui.expansion(text="Query Stats", value=True):
                ui.label("ToDo:")

    def show_entity_usage(self):
        """
        show entity usage in the queries
        """
        stats = QUERY_ITEM_STATS.get_entity_stats()
        records = [{"name": stat.label, "count": stat.count, "id": stat.identifier} for stat in stats]
        df = DataFrame.from_records(records).sort_values(by="count", ascending=False)
        fig = px.bar(df, x="name", y="count", title="Entity usage in queries")
        with self.input_row:
            ui.plotly(fig).classes("w-full")

    def show_property_usage(self):
        """
        show property usage in the queries
        """
        stats = QUERY_ITEM_STATS.get_property_stats()
        records = [{"name": stat.label, "count": stat.count} for stat in stats]
        df = DataFrame.from_records(records).sort_values(by="count", ascending=False)
        fig = px.bar(df, x="name", y="count", title="Property usage in queries")
        with self.input_row:
            ui.plotly(fig).classes("w-full")

    def show_keyword_usage(self):
        stats = QUERY_ITEM_STATS.get_keywords_stats()
        records = [{"name": stat.keyword, "count": stat.count} for stat in stats]
        df = DataFrame.from_records(records).sort_values(by="count", ascending=False)
        fig = px.bar(df, x="name", y="count", title="SPARQL keyword usage in queries")
        with self.input_row:
            ui.plotly(fig).classes("w-full")

    def show_function_usage(self):
        stats = QUERY_ITEM_STATS.get_function_stats()
        records = [{"name": stat.name, "count": stat.count} for stat in stats]
        df = DataFrame.from_records(records).sort_values(by="count", ascending=False)
        fig = px.bar(df, x="name", y="count", title="SPARQL function usage in queries")
        with self.input_row:
            ui.plotly(fig).classes("w-full")

    def show_namespace_usage(self):
        stats = QUERY_ITEM_STATS.get_namespace_stats()
        records = [{"name": stat.prefix, "count": stat.count} for stat in stats]
        df = DataFrame.from_records(records).sort_values(by="count", ascending=False)
        fig = px.bar(df, x="name", y="count", title="Namespaces used in SPARQL queries")
        with self.input_row:
            ui.plotly(fig).classes("w-full")
