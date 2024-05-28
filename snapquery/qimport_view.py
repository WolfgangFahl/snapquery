"""
Created on 2024-05-05

@author: wf
"""

from typing import Optional

from lodstorage.query import Query, QuerySyntaxHighlight
from nicegui import ui

from snapquery.models.person import Person
from snapquery.person_selector import PersonView
from snapquery.qimport import QueryImport
from snapquery.snapquery_core import NamedQuery


class QueryImportView:
    """
    display Query Import UI
    """

    def __init__(
        self,
        solution=None,
        person: Optional[Person] = None,
        allow_importing_from_url: bool = True,
    ):
        self.person = person
        self.solution = solution
        self.allow_importing_from_url = allow_importing_from_url
        self.namespace = ""
        self.name = ""
        self.url = ""
        self.title = ""
        self.description = ""
        self.query = None
        if self.solution:
            self.qimport = QueryImport()
            self.nqm = self.solution.nqm
            self.setup_ui()

    def setup_ui(self):
        """
        setup the user interface
        """
        with self.solution.container:
            with ui.row() as self.input_row:
                ui.input(
                    label="namespace", placeholder="e.g. wikidata-examples"
                ).bind_value(self, "namespace")
                with ui.input(
                    label="name", placeholder="e.g. all proceedings of CEUR-WS"
                ).bind_value(self, "name"):
                    ui.tooltip(
                        "short name for query; needs to be unique within the namespace"
                    )
                ui.input(label="url", placeholder="e.g. short url to the query").props(
                    "size=80"
                ).bind_value(self, "url")
                if self.allow_importing_from_url:
                    ui.button(
                        icon="input", text="Import Query", on_click=self.on_input_button
                    )
                ui.button(
                    icon="publish", text="Publish Query", on_click=self.on_import_button
                )
            with ui.row() as self.details_row:
                with ui.input(label="title").props("size=80").bind_value(self, "title"):
                    ui.tooltip("Descriptive title of the query")
                ui.textarea(label="description").bind_value(self, "description")
                self.named_query_link = ui.html()
            self.query_row = ui.row().classes("w-full h-full ")
            with self.query_row:
                ui.textarea(label="query").bind_value(self, "query").classes(
                    "w-full h-full border-solid m-5 border-gray-dark border-2 rounded-md"
                )

    def on_import_button(self, _args):
        """
        import a query
        """
        if self.query is None:
            with self.query_row:
                ui.notify("input a query first")
            return
        nq_record = {
            "namespace": self.namespace,
            "name": self.name,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "sparql": self.query.query,
        }
        nq = NamedQuery.from_record(nq_record)
        self.nqm.add_and_store(nq)
        with self.query_row:
            ui.notify(f"added named query {self.name}")
            self.named_query_link.content = nq.as_link()

    def on_input_button(self, _args):
        """
        imput a query
        """
        self.query_row.clear()
        with self.query_row:
            ui.notify(f"importing named query from {self.url}")
            sparql_query = self.qimport.read_from_short_url(self.url)
            self.query = Query(
                name=self.name, title=self.title, lang="sparql", query=sparql_query
            )
            query_syntax_highlight = QuerySyntaxHighlight(self.query)
            syntax_highlight_css = query_syntax_highlight.formatter.get_style_defs()
            ui.add_css(syntax_highlight_css)
            ui.html(query_syntax_highlight.highlight())
