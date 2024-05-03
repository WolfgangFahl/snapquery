'''
Created on 2024-05-03

@author: wf
'''
import asyncio
from nicegui import ui
from ngwidgets.lod_grid import ListOfDictsGrid

class NamedQuerySearch:
    """
    search for namedqueries
    """
    def __init__(self,solution):
        self.solution=solution
        self.nqm=self.solution.nqm
        self.search_debounce_task=None
        self.keystroke_time = 0.65  # minimum time in seconds to wait between keystrokes before starting searching
        self.setup_ui()
        
    def setup_ui(self):
        """
        setup my user interface
        """
        with ui.row() as self.search_row:
            self.search_input = ui.input(
                label="search", on_change=self.on_search_change
            ).props("size=80")
        with ui.row() as self.search_result_row:
            self.search_result_grid = ListOfDictsGrid()
            
    async def on_search_change(self, _args):
        """
        react on changes in the search input
        """
        # Cancel the existing search task if it's still waiting
        if self.search_debounce_task:
            self.search_debounce_task.cancel()

        # Create a new task for the new search
        self.search_debounce_task = asyncio.create_task(self.debounced_search())

    async def debounced_search(self):
        """
        Waits for a period of inactivity and then performs the search.
        """
        try:
            # Wait for the debounce period (keystroke_time)
            await asyncio.sleep(self.keystroke_time)
            search_for = self.search_input.value
            sql_query="SELECT * FROM NamedQuery WHERE name LIKE ?"
            search_like=f"{search_for}%"
            q_lod = self.nqm.sql_db.query(sql_query,(search_like,))
            view_lod=q_lod
            if self.search_result_row:
                with self.search_result_row:
                    ui.notify(f"found {len(q_lod)} queries")
                    self.search_result_grid.load_lod(view_lod)
                    # self.search_result_grid.set_checkbox_selection("#")
                    self.search_result_grid.update()
                    
        except asyncio.CancelledError:
            # The search was cancelled because of new input, so just quietly exit
            pass
        except BaseException as ex:
            self.solution.handle_exception(ex)