"""
Created on 2024-05-05

@author: wf
"""

from typing import Optional

from lodstorage.query import Query, QuerySyntaxHighlight
from nicegui import ui

from snapquery.models.person import Person
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
        self.comment = ""
        self.query = None
        if self.solution:
            self.qimport = QueryImport()
            self.nqm = self.solution.nqm
            self.setup_ui()

    def setup_ui(self):
        """
        setup the user interface
        """
        if self.solution.user_has_llm_right:
            self.setup_ui_llm()
        else:
            self.setup_ui_public()

    def setup_ui_llm(self):
        with self.solution.container:
            with ui.column():
                ui.textarea(label="URL List", placeholder="Paste short URLs, one per line").bind_value(self, "url_list")
                ui.button(icon="input", text="Import Queries", on_click=self.on_input_multiple_urls)

    def on_input_multiple_urls(self, _args):
        urls = self.url_list.strip().split('\n')
        for url in urls:
            sparql_query = self.qimport.read_from_short_url(url)

    def setup_ui_public(self):
        """
        setup the user interface for a public user that needs to identify
        """
        with self.solution.container:
            with ui.row() as self.input_row:
                self.input_row.classes("h-full")
                ui.input(label="namespace", placeholder="e.g. wikidata-examples").bind_value(self, "namespace")
                with ui.input(label="name", placeholder="e.g. all proceedings of CEUR-WS").bind_value(self, "name"):
                    ui.tooltip("short name for query; needs to be unique within the namespace")
                ui.input(label="url", placeholder="e.g. short url to the query").props("size=80").bind_value(
                    self, "url"
                )
                if self.allow_importing_from_url:
                    ui.button(icon="input", text="Import Query", on_click=self.on_input_button)
                ui.button(icon="publish", text="Publish Query", on_click=self.on_import_button)
                with ui.input(label="title").props("size=80").bind_value(self, "title"):
                    ui.tooltip("Descriptive title of the query")
            self.query_row = ui.row().classes("w-full h-full flex ")
            with self.query_row:
                ui.textarea(label="query").bind_value(self, "query").classes(
                    "w-full h-full resize min-h-80 border-solid m-5 border-gray-dark border-2 rounded-md"
                )
            with ui.row() as self.details_row:
                self.details_row.classes("flex")
                ui.textarea(label="description").bind_value(self, "description").classes(
                    "w-1/2 border-solid m-5 border-gray-dark border-2 rounded-md"
                )
                ui.textarea(label="comment").bind_value(self, "comment").classes(
                    "w-2/5 border-solid m-5 border-gray-dark border-2 rounded-md"
                )
                self.named_query_link = ui.html()

    def on_import_button(self, _args):
        """
        import a query
        """
        if self.query is None:
            with self.query_row:
                ui.notify("input a query first")
            return
        if self.person:
            self.comment = f"[query nominated by {self.person}] {self.comment}"
        nq_record = {
            "namespace": self.namespace,
            "name": self.name,
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "comment": self.comment,
            "sparql": self.query.query if isinstance(self.query, Query) else self.query,
        }
        nq = NamedQuery.from_record(nq_record)
        self.nqm.add_and_store(nq)
        with self.query_row:
            ui.notify(f"added named query {self.name}")
            self.named_query_link.content = nq.as_link()
        self.clear_inputs()

    def clear_inputs(self):
        self.query = None
        self.name = None
        self.url = None
        self.title = None
        self.description = None
        self.comment = None

    def on_input_button(self, _args):
        """
        imput a query
        """
        self.query_row.clear()
        with self.query_row:
            ui.notify(f"importing named query from {self.url}")
            sparql_query = self.qimport.read_from_short_url(self.url)
            self.query = Query(name=self.name, title=self.title, lang="sparql", query=sparql_query)
            query_syntax_highlight = QuerySyntaxHighlight(self.query)
            syntax_highlight_css = query_syntax_highlight.formatter.get_style_defs()
            ui.add_css(syntax_highlight_css)
            ui.html(query_syntax_highlight.highlight())
