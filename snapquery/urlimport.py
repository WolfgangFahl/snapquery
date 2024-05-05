"""
Created on 2024-05-05

@author: wf
"""
from nicegui import ui

class UrlImport:
    """
    import named queries from a given url
    """
    
    def __init__(self,solution):
        self.solution=solution
        self.setup_ui()
        self.namespace=""
        self.url=""
        
    def setup_ui(self):
        with self.solution.container:
            with ui.row() as self.input_row:
                ui.input(label="namespace").bind_value(self,"namespace")
                ui.input(label="url").bind_value(self,"url")
                ui.button(icon="play_arrow", on_click=self.import_query)
 
    def import_query(self,_args):
        """
        import a query
        """
        with self.input_row:
            ui.notify(f"importing named query from {self.url}")