"""
Created on 2024-07-04
@author: wf
"""
from typing import List
from nicegui import ui
from ngwidgets.webserver import WebSolution
from snapquery.snapquery_core import QueryName, QueryNameSet
from ngwidgets.combobox import ComboBox

class QuerySelector:
    """
    A class to select domain, namespace, and name for a query using comboboxes.
    Uses a single change handler to update selections dynamically.
    """
    def __init__(self, solution: WebSolution, on_change):
        self.solution = solution
        self.nqm = self.solution.nqm
        self.qns = QueryNameSet(self.nqm)  # Initialize QueryNameSet
        self.qn = QueryName(domain="", namespace="", name="")  # Current selection state
        self.qns.update(domain=self.qn.domain, namespace=self.qn.namespace)
        self.on_change = on_change
        self.setup_ui()

    def setup_ui(self):
        """
        Setup the user interface for query selection using comboboxes.
        """
        with ui.row() as self.select_row:
            self.domain_select = self.create_combobox("Domain", self.qns.domains, 25)
            self.namespace_select = self.create_combobox("Namespace", self.qns.namespaces, 40)
            self.name_select = self.create_combobox("Name", self.qns.names, 80)

    def create_combobox(self, label: str, options: List[str], width_chars: int) -> ComboBox:
        """Create a ComboBox with the given label, options, and width."""
        return ComboBox(
            label=label,
            options=options,
            width_chars=width_chars,
            clearable=True,
            on_change=self.handle_change
        )

    async def handle_change(self):
        """
        Update self.qn and call the provided on_change callback
        """
        self.qn.domain = self.domain_select.select.value or ""
        self.qn.namespace = self.namespace_select.select.value or ""
        self.qn.name = self.name_select.select.value or ""
        
        self.qns.update(domain=self.qn.domain, namespace=self.qn.namespace)
        self.update_ui()
        
        if self.on_change:
            await self.on_change()    
            
    def update_options(self,select_widget,options):  
        select_widget.update_options(options)
     
    def update_ui(self):
        """
        Update UI components based on filtered results using the custom update_options method for safe sorting.
        """
        self.update_options(self.domain_select, self.qns.domains)
        self.update_options(self.namespace_select, self.qns.namespaces)
        self.update_options(self.name_select, self.qns.names)