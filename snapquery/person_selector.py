"""
Created 2023

@author: th
"""

from typing import Any, Callable, List, Optional

from ngwidgets.input_webserver import WebSolution
from nicegui import run, ui
from nicegui.element import Element

from snapquery.models.person import Person
from snapquery.pid_lookup import PersonLookup
from snapquery.pid import PIDs, PIDValue


class PersonSuggestion(Element):
    """
    Display a Person
    """

    def __init__(self, person: Person, on_select: Callable[[Person], Any]):
        self.pids = PIDs()
        self.pid_values = self._create_pid_values(person)
        super().__init__(tag="div")
        self.person = person
        self._on_select_callback = on_select
        with ui.item(on_click=self.on_select) as self.person_card:
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

    def on_select(self):
        """
        Handle selection of the suggestion card
        """
        return self._on_select_callback(self.person)

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


class PersonSelector:
    """
    Select a person with auto-suggestion
    """

    def __init__(self, solution: WebSolution, selection_callback: Callable[[Person], Any]):
        """
        Constructor
        """
        self.solution = solution
        self.selection_callback = selection_callback
        self.selected_person: Optional[Person] = None
        self.suggestion_list: Optional[ui.element] = None
        self.search_name = ""
        self.suggested_persons = []
        self.person_lookup = PersonLookup(nqm=solution.webserver.nqm)
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
                    with ui.card() as self.selection_card:
                        with ui.row():
                            self.label = ui.label(
                                "Please identify yourself by entering or looking up a valid PID(Wikidata ID, ORCID, dblp):"
                            )
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
                                on_change=self.suggest_persons,
                                value=person.wikidata_id,
                            ).props("size=20")
            with splitter.after:
                with ui.element("column").classes(" w-full h-full gap-2"):
                    self.suggestion_list = ui.column().classes(
                        "rounded-md border-2 p-3"
                    )

    async def suggest_persons(self):
        """
        based on given input suggest potential persons

        Returns:
            List of persons
        """
        try:
            self.search_name = self.name_input.value
            if (
                len(self.search_name) >= 4
            ):  # quick fix to avoid queries on empty input fields
                self.suggested_persons = await run.io_bound(
                    self.person_lookup.suggest_from_all, self.search_name
                )
                self.update_suggestion_list(
                    self.suggestion_list, self.suggested_persons
                )
        except Exception as ex:
            self.solution.handle_exception(ex)

    def update_suggestion_list(self, container: ui.element, suggestions: List[Person]):
        """
        update the suggestions list
        """
        container.clear()
        with container:
            with ui.list().props("bordered separator"):
                ui.item_label("Suggestions").props("header").classes("text-bold")
                ui.separator()
                for person in suggestions[:10]:
                    PersonSuggestion(
                        person=person, on_select=self.selection_callback
                    )

                if len(suggestions) > 10:
                    with ui.item():
                        ui.label(
                            f"{'>' if len(suggestions) == 10000 else ''}{len(suggestions)} matches are available..."
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
        if self.suggestion_list:
            self.suggestion_list.clear()
            self.suggested_persons = [person]
            self.update_suggestion_list(self.suggestion_list, self.suggested_persons)
