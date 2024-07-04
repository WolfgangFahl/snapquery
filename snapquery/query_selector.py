"""
Created on 2024-07-04
@author: wf
"""
from typing import Dict, List
from nicegui import ui
from ngwidgets.webserver import WebSolution
from snapquery.snapquery_core import QueryName, QueryNameSet
from ngwidgets.debouncer import DebouncerUI
from ngwidgets.combobox import ComboBox

class QuerySelector:
    """
    A class to select domain, namespace, and name for a query using comboboxes.
    Uses a single change handler to update selections dynamically.
    """
    def __init__(self, solution: WebSolution):
        self.solution = solution
        self.nqm = self.solution.nqm
        self.qns = QueryNameSet(self.nqm)  # Initialize QueryNameSet
        self.qn = QueryName(domain="", namespace="", name="")  # Current selection state
        self.qns.update(domain=self.qn.domain, namespace=self.qn.namespace)
        self.debouncer = DebouncerUI(self.solution, delay=0.3, debug=True)
        self.setup_ui()

    def setup_ui(self):
        """
        Setup the user interface for query selection using comboboxes.
        """
        with ui.row() as self.select_row:
            self.domain_select = ComboBox(
                label=f"Domain ({len(self.qns.domains)})",
                options=sorted(self.qns.domains),
                width_chars=35,
                on_change=self.on_change
            )
            self.namespace_select = ComboBox(
                label=f"Namespace ({len(self.qns.namespaces)})",
                options=sorted(self.qns.namespaces),
                width_chars=35,
                on_change=self.on_change
            )
            self.name_select = ComboBox(
                label=f"Name ({len(self.qns.names)})",
                options=sorted(self.qns.names),
                width_chars=35,
                on_change=self.on_change
            )
        self.on_change()  # Initial population and update of UI components
    
    def update_ui(self):
        """
        Update UI components based on filtered results
        """
        self.namespace_select.update_options(sorted(self.qns.namespaces))
        self.name_select.update_options(sorted(self.qns.names))
        
        # Update labels with counts
        self.domain_select.select.label = f"Domain ({len(self.qns.domains)})"
        self.namespace_select.select.label = f"Namespace ({len(self.qns.namespaces)})"
        self.name_select.select.label = f"Name ({len(self.qns.names)})"

    def on_change(self):
        """
        Handle changes to any of the selection boxes, updating relevant options and internal state.
        """
        # Update the current selections based on UI component values
        self.qn.domain = self.domain_select.select.value or ""
        self.qn.namespace = self.namespace_select.select.value or ""
        self.qn.name = self.name_select.select.value or ""
        
        if self.qn.domain and self.qn.namespace and self.qn.name:
            with self.select_row:
                ui.notify(f"You selected: {self.qn.name} in {self.qn.namespace} at {self.qn.domain}")
        else:
            # Update QueryNameSet with the current selections to filter domains and namespaces
            self.qns.update(domain=self.qn.domain, namespace=self.qn.namespace)
            self.update_ui()