"""
Created on 2024-05-06

@author: wf
"""
import re

from ngwidgets.dict_edit import DictEdit, FieldUiDef, FormUiDef


class Params:
    """
    parameter handling
    """

    def __init__(self, query: str):
        """
        constructor

        Args:
            query(str): the query to analyze for parameters
        """
        self.query = query
        self.pattern = re.compile(r"{{\s*(\w+)\s*}}")
        self.params = self.pattern.findall(query)
        self.params_dict = {param: "" for param in self.params}
        self.has_params = len(self.params) > 0

    def open(self):
        self.dict_edit.expansion.open()

    def close(self):
        self.dict_edit.expansion.close()

    def get_dict_edit(self) -> DictEdit:
        """
        Return a DictEdit instance for editing parameters.
        """
        # Define a custom form definition for the title "Params"
        form_ui_def = FormUiDef(
            title="Params",
            icon="tune",
            ui_fields={
                key: FieldUiDef.from_key_value(key, value)
                for key, value in self.params_dict.items()
            },
        )
        self.dict_edit = DictEdit(
            data_to_edit=self.params_dict, form_ui_def=form_ui_def
        )
        self.open()
        return self.dict_edit

    def apply_parameters(self) -> str:
        """
        Replace Jinja templates in the query with corresponding parameter values.

        Returns:
            str: The query with Jinja templates replaced by parameter values.
        """
        query = self.query
        for param, value in self.params_dict.items():
            pattern = re.compile(r"{{\s*" + re.escape(param) + r"\s*\}\}")
            query = re.sub(pattern, value, query)
        return query
