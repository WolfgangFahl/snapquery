"""
Created 2023

@author: th
"""
from typing import Any, Callable, List, Optional

from ngwidgets.input_webserver import WebSolution
from ngwidgets.profiler import Profiler
from nicegui import run, ui
from nicegui.element import Element

from snapquery.models.person import Person
from snapquery.services.dblp import Dblp
from snapquery.services.wikidata import Wikidata


class PersonSuggestion(Element):
    """
    display a Person
    """

    def __init__(self, person: Person, on_select: Callable[[Person], Any]):
        super().__init__(tag="div")
        self.person = person
        self._on_select_callback = on_select
        with ui.card().tight() as card:
            card.on("click", self.on_select)
            with ui.card_section() as section:
                section.props(add="horizontal")
                with ui.card_section():
                    with ui.avatar():
                        if person.image:
                            ui.image(source=person.image)
                ui.separator().props(add="vertical")
                with ui.card_section():
                    with ui.row():
                        self.person_label = ui.label(self.person.label)
                    with ui.row():
                        self.person_name = ui.label(
                            f"{self.person.given_name} {self.person.family_name}"
                        )
                    with ui.row():
                        self._show_identifier()

    def on_select(self):
        """
        Handle selection of the suggestion card
        """
        return self._on_select_callback(self.person)

    def _show_identifier(self):
        """
        display all identifier of the person
        """
        if self.person.wikidata_id:
            with ui.element("div"):
                ui.avatar(
                    icon="img:https://www.wikidata.org/static/favicon/wikidata.ico",
                    color=None,
                    size="sm",
                    square=True,
                )
                ui.link(
                    text=self.person.wikidata_id,
                    target=f"https://www.wikidata.org/wiki/{self.person.wikidata_id}",
                    new_tab=True,
                )
        if self.person.dblp_author_id:
            with ui.element("div"):
                ui.element("i").classes("ai ai-dblp")
                ui.link(
                    text=self.person.dblp_author_id,
                    target=f"https://dblp.org/pid/{self.person.dblp_author_id}",
                    new_tab=True,
                )
        if self.person.orcid_id:
            with ui.element("div"):
                ui.element("i").classes("ai ai-orcid")
                ui.link(
                    text=self.person.orcid_id,
                    target=f"https://orcid.org/{self.person.orcid_id}",
                    new_tab=True,
                )


class PersonSelector:
    """
    Select a person with auto-suggestion
    """

    def __init__(self, solution: WebSolution):
        """
        Constructor
        """
        self.solution = solution
        self.profilers = {
            "dblp": Profiler("dblp search", profile=True, with_start=False),
            "wikidata": Profiler("wikidata search", profile=True, with_start=False),
        }
        ui.add_head_html(
            '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/jpswalsh/academicons@1/css/academicons.min.css">'
        )
        self.selected_person: Optional[Person] = None
        self.suggestion_list_wd: Optional[ui.element] = None
        self.suggestion_list_dblp: Optional[ui.element] = None
        self.person_selection()

    @ui.refreshable
    def person_selection(self):
        """
        Display input fields for person data with auto suggestion
        """
        person = self.selected_person if self.selected_person else Person()
        with ui.element("div").classes("w-full"):
            with ui.splitter().classes("h-full  w-full") as splitter:
                with splitter.before:
                    with ui.row():
                        self.label=ui.label("Please identify yourself:")
                    with ui.row():
                        self.given_name_input = ui.input(
                            label="given_name",
                            placeholder="""given name""",
                            on_change=self.suggest_persons,
                            value=person.given_name,
                        )
                        self.family_name_input = ui.input(
                            label="family_name",
                            placeholder="""family name""",
                            on_change=self.suggest_persons,
                            value=person.family_name,
                        )
                    with ui.row():
                        self.identifier_input = ui.input(
                            label="identifier",
                            placeholder="""identifier-""",
                            on_change=self.suggest_persons,
                            value=person.wikidata_id,
                        )
                    with ui.row():
                        self.identifier_type_input = ui.radio(
                            options={
                                "wikidata_id": "Wikidata",
                                "dblp_author_id": "dblp",
                                "orcid_id": "ORCID",
                            },
                            value="wikidata_id",
                            on_change=self.suggest_persons,
                        ).props("inline")
                with splitter.after:
                    with ui.element("div").classes("columns-2 w-full h-full gap-2"):
                        ui.label("wikidata")
                        self.suggestion_list_wd = ui.column().classes(
                            "rounded-md border-2 p-3"
                        )

                        ui.label("dblp")
                        self.suggestion_list_dblp = ui.column().classes(
                            "rounded-md border-2"
                        )

    async def suggest_persons(self):
        """
        based on given input suggest potential persons

        Returns:
            List of persons
        """
        search_mask = self._get_search_mask()
        name = search_mask.name
        if len(name) >= 6:  # quick fix to avoid queries on empty input fields
            self.profilers["dblp"].start()
            suggested_persons_dblp = await run.io_bound(
                Dblp().get_person_suggestions, search_mask
            )
            self.update_suggestion_list(
                self.suggestion_list_dblp, suggested_persons_dblp
            )
            self.profilers["dblp"].time(f" {name}")
            self.profilers["wikidata"].start()
            suggested_persons_wd = await run.io_bound(
                Wikidata().get_person_suggestions, search_mask
            )
            self.profilers["wikidata"].time(f" {name}")
            self.update_suggestion_list(self.suggestion_list_wd, suggested_persons_wd)

    def update_suggestion_list(self, container: ui.element, suggestions: List[Person]):
        """
        update the suggestions list
        """
        container.clear()
        with container:
            if len(suggestions) <= 10:
                with ui.scroll_area():
                    for person in suggestions:
                        PersonSuggestion(
                            person=person, on_select=self.select_person_suggestion
                        )
            else:
                ui.spinner(size="lg")
                ui.label(
                    f"{'>' if len(suggestions) == 10000 else ''}{len(suggestions)} matches..."
                )
        return []

    def select_person_suggestion(self, person: Person):
        """
        Select the given Person by updating the input fields to the selected person and storing teh object internally
        Args:
            person: person that should be selected
        """
        self.selected_person = person
        self.person_selection.refresh()
        if self.suggestion_list_wd:
            self.suggestion_list_wd.clear()
        if self.suggestion_list_dblp:
            self.suggestion_list_dblp.clear()

    def _get_search_mask(self) -> Person:
        """
        Get the current search mask from the input fields
        Returns:
            PersonSearchMask: current search input
        """
        ids = dict()
        if self.identifier_type_input.value:
            ids[self.identifier_type_input.value] = self.identifier_input.value
        search_mask = Person(
            label=None,
            given_name=self.given_name_input.value,
            family_name=self.family_name_input.value,
            **ids,
        )
        return search_mask
