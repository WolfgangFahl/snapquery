"""
Created 2023

@author: th
"""
from typing import Any, Callable, List, Optional

from ngwidgets.input_webserver import WebSolution
from ngwidgets.profiler import Profiler
from nicegui import run, ui
from nicegui.element import Element

from snapquery.models.scholar import Scholar
from snapquery.services.dblp import Dblp
from snapquery.services.wikidata import Wikidata


class ScholarSuggestion(Element):
    """
    display a Scholar
    """

    def __init__(self, scholar: Scholar, on_select: Callable[[Scholar], Any]):
        super().__init__(tag="div")
        self.scholar = scholar
        self._on_select_callback = on_select
        with ui.card().tight() as card:
            card.on("click", self.on_select)
            with ui.card_section() as section:
                section.props(add="horizontal")
                with ui.card_section():
                    with ui.avatar():
                        if scholar.image:
                            ui.image(source=scholar.image)
                ui.separator().props(add="vertical")
                with ui.card_section():
                    with ui.row():
                        self.scholar_label = ui.label(self.scholar.label)
                    with ui.row():
                        self.scholar_name = ui.label(
                            f"{self.scholar.given_name} {self.scholar.family_name}"
                        )
                    with ui.row():
                        self._show_identifier()

    def on_select(self):
        """
        Handle selection of the suggestion card
        """
        return self._on_select_callback(self.scholar)

    def _show_identifier(self):
        """
        display all identifier of the scholar
        """
        if self.scholar.wikidata_id:
            with ui.element("div"):
                ui.avatar(
                    icon="img:https://www.wikidata.org/static/favicon/wikidata.ico",
                    color=None,
                    size="sm",
                    square=True,
                )
                ui.link(
                    text=self.scholar.wikidata_id,
                    target=f"https://www.wikidata.org/wiki/{self.scholar.wikidata_id}",
                    new_tab=True,
                )
        if self.scholar.dblp_author_id:
            with ui.element("div"):
                ui.element("i").classes("ai ai-dblp")
                ui.link(
                    text=self.scholar.dblp_author_id,
                    target=f"https://dblp.org/pid/{self.scholar.dblp_author_id}",
                    new_tab=True,
                )
        if self.scholar.orcid_id:
            with ui.element("div"):
                ui.element("i").classes("ai ai-orcid")
                ui.link(
                    text=self.scholar.orcid_id,
                    target=f"https://orcid.org/{self.scholar.orcid_id}",
                    new_tab=True,
                )


class ScholarSelector:
    """
    Select a scholar with auto-suggestion
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
        self.selected_scholar: Optional[Scholar] = None
        self.suggestion_list_wd: Optional[ui.element] = None
        self.suggestion_list_dblp: Optional[ui.element] = None
        self.scholar_selection()

    @ui.refreshable
    def scholar_selection(self):
        """
        Display input fields for scholar data with autosuggestion
        """
        scholar = self.selected_scholar if self.selected_scholar else Scholar()
        with ui.element("div").classes("w-full"):
            with ui.splitter().classes("h-full  w-full") as splitter:
                with splitter.before:
                    with ui.row():
                        self.given_name_input = ui.input(
                            label="given_name",
                            placeholder="""given name""",
                            on_change=self.suggest_scholars,
                            value=scholar.given_name,
                        )
                        self.family_name_input = ui.input(
                            label="family_name",
                            placeholder="""family name""",
                            on_change=self.suggest_scholars,
                            value=scholar.family_name,
                        )
                    with ui.row():
                        self.identifier_type_input = ui.radio(
                            options={
                                "wikidata_id": "Wikidata",
                                "dblp_author_id": "dblp",
                                "orcid_id": "ORCID",
                            },
                            value="wikidata_id",
                            on_change=self.suggest_scholars,
                        ).props("inline")
                        self.identifier_input = ui.input(
                            label="identifier",
                            placeholder="""identifier-""",
                            on_change=self.suggest_scholars,
                            value=scholar.wikidata_id,
                        )
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

    async def suggest_scholars(self):
        """
        based on given input suggest potential scholars

        Returns:
            List of scholars
        """
        search_mask = self._get_search_mask()
        name = search_mask.name
        if len(name) >= 6:  # quick fix to avoid queries on empty input fields
            self.profilers["dblp"].start()
            suggested_scholars_dblp = await run.io_bound(
                Dblp().get_scholar_suggestions, search_mask
            )
            self.update_suggestion_list(
                self.suggestion_list_dblp, suggested_scholars_dblp
            )
            self.profilers["dblp"].time(f" {name}")
            self.profilers["wikidata"].start()
            suggested_scholars_wd = await run.io_bound(
                Wikidata().get_scholar_suggestions, search_mask
            )
            self.profilers["wikidata"].time(f" {name}")
            self.update_suggestion_list(self.suggestion_list_wd, suggested_scholars_wd)

    def update_suggestion_list(self, container: ui.element, suggestions: List[Scholar]):
        """
        update the suggestions list
        """
        container.clear()
        with container:
            if len(suggestions) <= 10:
                with ui.scroll_area():
                    for scholar in suggestions:
                        ScholarSuggestion(
                            scholar=scholar, on_select=self.select_scholar_suggestion
                        )
            else:
                ui.spinner(size="lg")
                ui.label(
                    f"{'>' if len(suggestions) == 10000 else ''}{len(suggestions)} matches..."
                )
        return []

    def select_scholar_suggestion(self, scholar: Scholar):
        """
        Select the given Scholar by updating the input fields to the selected scholar and storing teh object internally
        Args:
            scholar: scholar that should be selected
        """
        self.selected_scholar = scholar
        self.scholar_selection.refresh()
        if self.suggestion_list_wd:
            self.suggestion_list_wd.clear()
        if self.suggestion_list_dblp:
            self.suggestion_list_dblp.clear()

    def _get_search_mask(self) -> Scholar:
        """
        Get the current search mask from the input fields
        Returns:
            ScholarSearchMask: current search input
        """
        ids = dict()
        if self.identifier_type_input.value:
            ids[self.identifier_type_input.value] = self.identifier_input.value
        search_mask = Scholar(
            label=None,
            given_name=self.given_name_input.value,
            family_name=self.family_name_input.value,
            **ids,
        )
        return search_mask
