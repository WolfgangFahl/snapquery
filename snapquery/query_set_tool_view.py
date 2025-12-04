"""
Created on 2024-05-05

@author: wf
"""

from lodstorage.query import Query, QuerySyntaxHighlight
from nicegui import background_tasks, ui

from snapquery.models.person import Person
from snapquery.person_selector import PersonSelector, PersonView
from snapquery.query_set_tool import QuerySetTool
from snapquery.snapquery_core import NamedQuery
from snapquery.wd_short_url import ShortUrl


class QuerySetToolView:
    """
    display Query Import UI
    """

    def __init__(
        self,
        solution=None,
    ):
        self.person = None
        self.solution = solution
        self.domain = "wikidata.org"
        self.namespace = "short_url"
        self.name = ""
        self.url = ""
        self.title = ""
        self.description = ""
        self.comment = ""
        self.query = None
        self.allow_importing_from_url = self.solution.user_has_llm_right
        if self.solution:
            self.qimport = QuerySetTool()
            self.nqm = self.solution.nqm

    def on_select_person(self, person: Person = None):
        """
        react on a person having been selected

        Args:
            person (Person): the selected Person (if any)
        """
        self.container.clear()
        with self.container:
            with ui.row().classes("w-full"):
                with ui.column():
                    ui.label(text="Nominate your Query").classes("text-xl")
                    ui.link(
                        text="see the documentation for detailed information on the nomination procedure",
                        new_tab=True,
                        target="https://wiki.bitplan.com/index.php/Snapquery#nominate",
                    )
                if person:
                    PersonView(person).classes("ml-auto bg-slate-100 rounded-md")
        with ui.row().classes("w-full"):
            self.setup_ui_public()

    def nominate_ui(self):
        """
        query nomination ui
        """
        with self.solution.container as self.container:
            with ui.column():
                ui.label(text="Nominate your Query").classes("text-xl")
                ui.link(
                    text="see the documentation for detailed information on the nomination procedure",
                    new_tab=True,
                    target="https://wiki.bitplan.com/index.php/Snapquery#nominate",
                )
                ui.label("Please identify yourself by entering or looking up a valid PID(Wikidata ID, ORCID, dblp).")
                self.person_selector = PersonSelector(solution=self.solution, selection_callback=self.on_select_person)

    def setup_ui_public(self):
        """
        setup the general public user interface common for
        both users that need to identify and those that are preauthorized
        """
        with self.solution.container:
            with ui.row() as self.input_row:
                self.input_row.classes("h-full")
                ui.input(label="domain", placeholder="e.g. short").bind_value(self, "domain")
                ui.input(label="namespace", placeholder="e.g. wikidata-examples").bind_value(self, "namespace")
                with ui.input(label="name", placeholder="e.g. all proceedings of CEUR-WS").bind_value(self, "name"):
                    ui.tooltip("short name for query; needs to be unique within the namespace")
            with ui.row() as self.url_row:
                ui.input(label="url", placeholder="e.g. short url to the query").props("size=80").bind_value(
                    self, "url"
                )
                if self.allow_importing_from_url:
                    ui.button(icon="input", text="Import Query", on_click=self.on_import_button)
                ui.button(icon="publish", text="Publish Query", on_click=self.on_publish_button)
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

    def on_publish_button(self, _args):
        """
        publish a query
        """
        if self.query is None:
            with self.query_row:
                ui.notify("input a query first")
            return
        if self.person:
            self.comment = f"[query nominated by {self.person}] {self.comment}"
        nq_record = {
            "domain": self.domain,
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
        """
        clear the inputs
        """
        self.query = None
        self.name = None
        self.url = None
        self.title = None
        self.description = None
        self.comment = None

    async def process_input(self):
        """
        Process input in background
        """
        try:
            short_url = ShortUrl(self.url)
            nq = self.qimport.read_from_short_url(short_url, domain=self.domain, namespace=self.namespace)
            if not nq:
                with self.query_row:
                    ui.notify(f"Could not read {short_url}")
                    return
            # we assume llm authorization is active here
            llm = ShortUrl.get_llm()
            _unique_urls, unique_names = self.nqm.get_unique_sets(domain="wikidata.org", namespace="short_url")
            llm_nq = short_url.ask_llm_for_name_and_title(llm=llm, nq=nq, unique_names=unique_names)
            with self.query_row:
                if not llm_nq:
                    ui.notify("LLM query failed")
                else:
                    self.title = nq.title
                    self.description = nq.description
                    self.name = nq.name
                self.query = Query(name=self.name, title=self.title, lang="sparql", query=nq.sparql)
                query_syntax_highlight = QuerySyntaxHighlight(self.query)
                syntax_highlight_css = query_syntax_highlight.formatter.get_style_defs()
                ui.add_css(syntax_highlight_css)
                self.query_row.clear()
                ui.html(query_syntax_highlight.highlight())
                self.query_row.update()
                pass
        except Exception as ex:
            self.solution.handle_exception(ex)

    async def on_import_button(self, _args):
        """
        input a query
        """
        try:
            self.query_row.clear()
            with self.query_row:
                ui.notify(f"importing named query from {self.url}")
                ui.spinner()
                self.query_row.update()
            self.search_task = background_tasks.create(self.process_input())
        except Exception as ex:
            self.solution.handle_exception(ex)
