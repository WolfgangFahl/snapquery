"""
Created 2023

@author: th
"""
import asyncio
from typing import Any, Callable, List, Optional

from ngwidgets.input_webserver import WebSolution
from nicegui import run, ui
from nicegui.element import Element
from nicegui.elements.button import Button

from snapquery.models.person import Person
from snapquery.pid import PIDs, PIDValue
from snapquery.pid_lookup import PersonLookup


class PersonView(Element):
    """
    Display a person
    """

    def __init__(self, person: Person):
        self.pids = PIDs()
        self.pid_values = self._create_pid_values(person)
        super().__init__(tag="div")
        self.person = person
        with self:
            with ui.item() as self.person_card:
                with ui.item_section().props("avatar"):
                    with ui.avatar():
                        if person.image:
                            ui.image(source=person.image)
                with ui.item_section():
                    with ui.row():
                        self.person_label = ui.label(self.person.label)
                    with ui.row():
                        self.person_name = ui.label(
                            f"{self.person.given_name} {self.person.family_name}"
                        )
                    with ui.row():
                        self._show_identifier()

    def _create_pid_values(self, person: Person) -> List[PIDValue]:
        """
        Create PIDValue instances for the person's identifiers
        """
        pid_values = []
        for pid_key, pid in self.pids.pids.items():
            attr = f"{pid_key}_id"
            pid_value = getattr(person, attr, None)
            if pid_value:
                pid_values.append(PIDValue(pid=pid, value=pid_value))
        return pid_values

    def _show_identifier(self):
        """
        Display all identifiers of the person
        """
        for pid_value in self.pid_values:
            with ui.element("div"):
                ui.avatar(
                    icon=f"img:{pid_value.pid.logo}",
                    color=None,
                    size="sm",
                    square=True,
                )
                ui.link(
                    text=pid_value.value,
                    target=pid_value.url,
                    new_tab=True,
                )


class PersonSuggestion(PersonView):
    """
    Display a Person
    """

    def __init__(self, person: Person, on_select: Callable[[Person], Any]):
        super().__init__(person=person)
        self._on_select_callback = on_select
        self.person_card.on_click(self.on_select)

    def on_select(self):
        """
        Handle selection of the suggestion card
        """
        return self._on_select_callback(self.person)


class PersonSelector:
    """
    Select a person with auto-suggestion
    """

    def __init__(
        self,
        solution: WebSolution,
        selection_callback: Callable[[Person], Any],
        limit: int = 10,
    ):
        """
        Constructor
        """
        # parameters
        self.solution = solution
        self.selection_callback = selection_callback
        self.limit = limit
        # instance variables
        self.suggested_persons: List[Person] = []
        self.selected_person: Optional[Person] = None
        self.suggestion_view: Optional[ui.element] = None
        self.search_name = ""
        self.person_lookup = PersonLookup(nqm=solution.webserver.nqm)
        self.selection_btn: Optional[Button] = None
        self.search_debounce_task = None
        self.keyStrokeTime = 0.5  # Debouncing interval in seconds
        self.spinner = None  # Spinner to indicate loading
        self.person_selection()

    @ui.refreshable
    def person_selection(self):
        """
        Display input fields for person data with auto-suggestion
        """
        person = self.selected_person if self.selected_person else Person()
        with ui.element("row").classes("w-full h-full"):
            with ui.splitter().classes("h-full  w-full") as splitter:
                with splitter.before:
                    with ui.row() as self.top_row:
                        pass
                    with ui.card() as self.selection_card:
                        with ui.row():
                            self.label = ui.label("Name or Pid:")
                        with ui.row():
                            self.name_input = ui.input(
                                label="name",
                                placeholder="Tim Berners-Lee",
                                on_change=self.suggest_persons,
                                value=self.search_name,
                            ).props("size=60")
                        with ui.row():
                            self.identifier_input = ui.input(
                                label="PID",
                                placeholder="Q80",
                                on_change=self.check_pid,
                                value=person.wikidata_id,
                            ).props("size=20")
                        # if self.selection_btn is None:
                        self.selection_btn = ui.button(
                            text="Continue", on_click=self.btn_selection_callback
                        )
                        self.selection_btn.disable()
            with splitter.after:
                with ui.element("column").classes(" w-full h-full gap-2"):
                    self.suggestion_view = ui.column().classes(
                        "rounded-md border-2 p-3"
                    )

    async def btn_selection_callback(self):
        person = Person()
        pid_value = PIDs().pid4id(self.identifier_input.value)
        if pid_value.pid.name == "Wikidata":
            person.wikidata_id = self.identifier_input.value
        elif pid_value.pid.name == "dblp":
            person.dblp_id = self.identifier_input.value
        elif pid_value.pid.name == "ORCID":
            person.orcid_id = self.identifier_input.value
        person.label = self.name_input.value
        self.selection_callback(person)

    async def check_pid(self):
        pid = PIDs().pid4id(self.identifier_input.value)
        if pid is not None and pid.is_valid() and self.selection_btn is not None:
            print("Is valid PID")
            self.selection_btn.enable()
        elif self.selection_btn:
            self.selection_btn.disable()
        ui.update()

    async def suggest_persons(self):
        """
        Based on given input suggest potential persons with debouncing.
        """
        if self.search_debounce_task:
            self.search_debounce_task.cancel()
            self.suggested_persons = []
            self.spinner.visible = False

        self.search_debounce_task = asyncio.create_task(
            self.debounced_suggest_persons()
        )
        if not self.spinner:
            with self.top_row:
                self.spinner = ui.spinner()

    async def debounced_suggest_persons(self):
        """
        Debounced version of suggest_persons.
        """
        try:
            await asyncio.sleep(self.keyStrokeTime)
            self.search_name = self.name_input.value
            if (
                len(self.search_name) >= 4
            ):  # quick fix to avoid queries on empty input fields
                # Get suggestions concurrently and update UI as results come in
                tasks = [
                    asyncio.create_task(
                        self.person_lookup.suggest_from_wikidata(
                            self.search_name, limit=self.limit
                        )
                    ),
                    asyncio.create_task(
                        self.person_lookup.suggest_from_orcid(
                            self.search_name, limit=self.limit
                        )
                    ),
                    asyncio.create_task(
                        self.person_lookup.suggest_from_dblp(
                            self.search_name, limit=self.limit
                        )
                    ),
                ]
                for future in asyncio.as_completed(tasks):
                    new_persons = await future
                    self.merge_and_update_suggestions(new_persons)
                self.spinner.visible = False  # Hide spinner when all tasks complete
        except asyncio.CancelledError:
            # If the task is cancelled, do nothing.
            pass
        except Exception as ex:
            self.solution.handle_exception(ex)

    def merge_and_update_suggestions(self, new_persons: List[Person]):
        """
        Merges new persons with existing ones based on shared identifiers or adds them if unique.
        Ensures no duplicates are present in the list of suggested persons.

        Args:
            new_persons (List[Person]): New person suggestions to be added or merged.
        """
        for new_person in new_persons:
            merged = False
            for existing_person in self.suggested_persons:
                if existing_person.share_identifier(new_person):
                    existing_person.merge_with(new_person)
                    merged = True
                    break
            if not merged:
                self.suggested_persons.append(new_person)

    def update_suggestions_view(self):
        """
        update the suggestions view
        """
        if self.suggestion_view:
            self.suggestion_view.clear()
            with self.suggestion_view:
                with ui.list().props("bordered separator"):
                    ui.item_label("Suggestions").props("header").classes("text-bold")
                    ui.separator()
                    for person in self.suggested_persons[: self.limit]:
                        PersonSuggestion(
                            person=person, on_select=self.selection_callback
                        )

                    if len(self.suggested_persons) > self.limit:
                        with ui.item():
                            ui.label(
                                f"{'>' if len(self.suggested_persons) >= 10000 else ''}{len(self.suggested_persons)} matches are available..."
                            )
            return []

    def select_person_suggestion(self, person: Person):
        """
        Select the given Person by updating the input fields to the selected person and storing the object internally
        Args:
            person: person that should be selected
        """
        self.selected_person = person
        self.person_selection.refresh()
        self.suggested_persons = [person]
        self.update_suggestions_list()
