'''
Created on 2024-05-05

@author: wf
'''
from lodstorage.query import Query, QuerySyntaxHighlight
from nicegui import ui
from snapquery.qimport import QueryImport
from snapquery.snapquery_core import NamedQuery

class QueryImportView:
    """
    display Query Import UI
    """
    def __init__(self, solution=None):
        self.solution = solution
        self.namespace = ""
        self.name = ""
        self.url = ""
        self.title = ""
        self.description = ""
        self.query=None
        if self.solution:
            self.qimport=QueryImport()
            self.nqm=self.solution.nqm
            self.setup_ui()

    def setup_ui(self):
        """
        setup the user interface
        """
        with self.solution.container:
            with ui.row() as self.input_row:
                ui.input(label="namespace").bind_value(self, "namespace")
                ui.input(label="name").bind_value(self, "name")
                ui.input(label="url").props("size=80").bind_value(self, "url")
                ui.button(icon="input", on_click=self.on_input_button)
                ui.button(icon="publish", on_click=self.on_import_button)
            with ui.row() as self.details_row:
                ui.input(label="title").props("size=80").bind_value(self, "title")
                ui.textarea(label="description").bind_value(self,"description")
                self.named_query_link=ui.html()
            self.query_row = ui.row()

    def on_import_button(self, _args):
        """
        import a query
        """
        if self.query is None:
            with self.query_row:
                ui.notify("input a query first")
            return
        nq_record={
            "namespace": self.namespace,
            "name":self.name,
            "title":self.title,
            "url": self.url,
            "description":self.description,
            "sparql":self.query.query,
        } 
        nq=NamedQuery.from_record(nq_record)
        lod=[]
        lod.append(nq_record)
        self.nqm.store(lod)
        with self.query_row:
            ui.notify(f"added named query {self.name}")
            self.named_query_link.content=nq.as_link()
        
    def on_input_button(self, _args):
        """
        imput a query
        """
        self.query_row.clear()
        with self.query_row:
            ui.notify(f"importing named query from {self.url}")
            sparql_query = self.qimport.read_from_short_url(self.url)
            self.query = Query(name=self.name,title=self.title,lang="sparql",query=sparql_query)
            query_syntax_highlight = QuerySyntaxHighlight(self.query)
            syntax_highlight_css = query_syntax_highlight.formatter.get_style_defs()
            ui.add_css(syntax_highlight_css)
            ui.html(query_syntax_highlight.highlight())