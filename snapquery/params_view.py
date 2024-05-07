"""
Created on 06.05.2024

@author: wf
"""
from lodstorage.params import Params
from ngwidgets.dict_edit import DictEdit, FieldUiDef, FormUiDef


class ParamsView:
    """
    a view for Query Parameters
    """

    def init(self, solution, params: Params):
        self.solution = solution
        self.params = params

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
                for key, value in self.params.params_dict.items()
            },
        )
        self.dict_edit = DictEdit(
            data_to_edit=self.params.params_dict, form_ui_def=form_ui_def
        )
        self.open()
        return self.dict_edit
