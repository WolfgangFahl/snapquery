"""
Created on 2024-05-03
@author: wf
"""

import json
from pathlib import Path

import fastapi
from fastapi import HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from lodstorage.query import Format
from ngwidgets.input_webserver import InputWebserver, InputWebSolution, WebserverConfig
from ngwidgets.login import Login
from ngwidgets.users import Users
from nicegui import app, ui
from nicegui.client import Client
from starlette.responses import JSONResponse, RedirectResponse

from snapquery.models.person import Person
from snapquery.namespace_stats_view import NamespaceStatsView
from snapquery.orcid import OrcidAuth
from snapquery.person_selector import PersonSelector, PersonView
from snapquery.qimport_view import QueryImportView
from snapquery.snapquery_core import NamedQueryManager, QueryBundle, QueryName, QueryPrefixMerger
from snapquery.snapquery_view import NamedQuerySearch, NamedQueryView
from snapquery.stats_view import QueryStatsView
from snapquery.version import Version
from snapquery.authorization import Authorization


class SnapQueryWebServer(InputWebserver):
    """
    server to supply named Queries
    """

    @classmethod
    def get_config(cls) -> WebserverConfig:
        """
        get the configuration for this Webserver
        """
        copy_right = ""
        config = WebserverConfig(
            short_name="snapquery",
            copy_right=copy_right,
            version=Version(),
            default_port=9862,
            timeout=6.0,
        )
        server_config = WebserverConfig.get(config)
        server_config.solution_class = SnapQuerySolution
        return server_config

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        InputWebserver.__init__(self, config=SnapQueryWebServer.get_config())
        users = Users("~/.solutions/snapquery")
        self.login = Login(self, users)
        self.orcid_auth = OrcidAuth(Path(self.config.base_path))
        self.authorization=Authorization.load()
        self.nqm = NamedQueryManager.from_samples()

        @ui.page("/admin")
        async def admin(client: Client):
            if not self.login.authenticated():
                return RedirectResponse("/login")
            return await self.page(client, SnapQuerySolution.admin_ui)

        @ui.page("/nominate")
        async def nominate(client: Client):
            return await self.page(client, SnapQuerySolution.nominate_ui)

        @ui.page("/stats")
        async def stats(client: Client):
            if not self.authenticated():
                return RedirectResponse("/login")
            return await self.page(client, SnapQuerySolution.stats_ui)

        @ui.page("/login")
        async def login(client: Client):
            return await self.page(client, SnapQuerySolution.login_ui)

        @app.get("/orcid_callback")
        async def orcid_authenticate_callback(code: str):
            try:
                self.orcid_auth.login(code)
            except Exception as e:
                return HTTPException(status_code=401, detail=str(e))
            return RedirectResponse("/")

        @ui.page("/logout")
        async def logout(client: Client) -> RedirectResponse:
            if self.login.authenticated():
                await self.login.logout()
            if self.orcid_auth.authenticated():
                self.orcid_auth.logout()
            return RedirectResponse("/")

        @ui.page("/queries_by_namespace")
        async def queries_by_namespace(client: Client):
            return await self.page(client, SnapQuerySolution.queries_by_namespace)

        @ui.page("/query/{domain}/{namespace}/{name}")
        async def query_page(
            client: Client,
            domain: str,
            namespace: str,
            name: str,
            endpoint_name: str = None,
            limit: int = None,
            format: str = "html",
        ):
            """
            show the query page for the given namespace and name
            """
            if endpoint_name is None:
                endpoint_name = SnapQuerySolution.get_user_endpoint()
            return await self.page(
                client,
                SnapQuerySolution.query_page,
                domain=domain,
                namespace=namespace,
                name=name,
                endpoint_name=endpoint_name,
                limit=limit,
                r_format_str=format,
            )

        @app.get("/api/endpoints")
        def get_endpoints():
            """
            list all endpoints
            """
            endpoints = self.nqm.endpoints
            return endpoints

        @app.get("/api/meta_query/{name}")
        def meta_query(name: str, limit: int = None):
            """
            run the meta query with the given name
            """
            name, r_format = self.get_r_format(name, "json")
            if name not in self.nqm.meta_qm.queriesByName:
                raise HTTPException(status_code=404, detail=f"meta query {name} not known")
            query = self.nqm.meta_qm.queriesByName[name]
            qb = QueryBundle(named_query=None, query=query)
            qlod = self.nqm.sql_db.query(query.query)
            if limit:
                qlod = qlod[:limit]
            content = qb.format_result(qlod, r_format)
            # content=content.replace("\n", "<br>\n")
            if r_format == Format.html:
                return HTMLResponse(content)
            return PlainTextResponse(content)

        @app.get("/api/sparql/{domain}/{namespace}/{name}")
        def sparql(
            domain: str,
            namespace: str,
            name: str,
            endpoint_name: str = "wikidata",
            limit: int = None,
        ) -> PlainTextResponse:
            """
            Gets a SPARQL query by name within a specified namespace

            Args:
                domain (str): The domain identifying the domain of the query.
                namespace (str): The namespace identifying the group or category of the query.
                name (str): The specific name of the query to be executed.
                endpoint_name (str): the name of the endpoint to use
                limit (int): a limit to set, default=None
            Returns:
                HTMLResponse: The plain text SPARQL code

            Raises:
                HTTPException: If the query cannot be found or fails to execute.
            """
            query_name = QueryName(domain=domain, namespace=namespace, name=name)
            qb = self.nqm.get_query(query_name=query_name, endpoint_name=endpoint_name, limit=limit)
            sparql_query = qb.query.query
            return PlainTextResponse(sparql_query)

        @app.get("/api/query/{domain}/{namespace}/{name}")
        def query(
            request: fastapi.Request,
            domain: str = fastapi.Path(
                description="The domain identifying the domain of the query", examples=["wikidata.org"]
            ),
            namespace: str = fastapi.Path(
                description="The namespace identifying the group or category of the query.",
                examples=["snapquery-examples"],
            ),
            name: str = fastapi.Path(description="The specific name of the query to be executed.", examples=["cats"]),
            endpoint_name: str = fastapi.Query(default="wikidata", examples=sorted(self.nqm.endpoints)),
            limit: int | None = fastapi.Query(default=None),
            format: Format | None = fastapi.Query(default=Format.html, exampes=[f.name for f in Format]),
        ):
            """
            Executes a SPARQL query by name within a specified namespace, formats the results, and returns them as an HTML response.

            Raises:
                HTTPException: If the query cannot be found or fails to execute.
            """
            content = self.query(
                name=name,
                namespace=namespace,
                domain=domain,
                endpoint_name=endpoint_name,
                limit=limit,
                param_dict=request.query_params,
                format=format,
            )
            if not content:
                raise HTTPException(status_code=500, detail="Could not create result")

            if format == Format.json:
                return JSONResponse(json.loads(content))

            return content

    def get_r_format(self, name: str, default_format_str: str = "html") -> Format:
        """
        get the result format from the given query name following the
        dot convention that <name>.<r_format_str> specifies the result format
        e.g. cats.json will ask for the json result format

        Args:
            name (str): the name of the query/meta query
            default_format_str (str): the name of the default format to use

        Returns:
            Format: the result format
        """
        if "." in name:
            r_format_str = name.split(".")[-1]
            name = name[: name.rfind(".")]
        else:
            r_format_str = default_format_str
        r_format = Format[r_format_str]
        return name, r_format

    def query(
        self,
        name: str,
        namespace: str,
        domain: str,
        endpoint_name: str = "wikidata",
        limit: int = None,
        param_dict=None,
        format=None,
    ) -> str:
        """
        Queries an external API to retrieve data based on a given namespace and name.

        Args:
            name (str): The name identifier of the data to be queried.
            namespace (str): The namespace to which the query belongs. It helps in categorizing the data.
            domain (str): The domain identifying the domain of the query.
            endpoint_name (str): The name of the endpoint to be used for the query. Defaults to 'wikidata'.
            limit (int): the limit for the query default: None

            Returns:
                str: the content retrieved
        """
        try:
            # content negotiation
            name, r_format = self.get_r_format(name)
            if format:
                r_format = format
            query_name = QueryName(domain=domain, namespace=namespace, name=name)
            qb = self.nqm.get_query(query_name=query_name, endpoint_name=endpoint_name, limit=limit)
            (qlod, stats) = qb.get_lod_with_stats(param_dict=param_dict)
            self.nqm.store_stats([stats])
            content = qb.format_result(qlod, r_format)
            return content
        except Exception as e:
            # Handling specific exceptions can be more detailed based on what nqm.get_sparql and nqm.query can raise
            raise HTTPException(status_code=404, detail=str(e))

    def authenticated(self) -> bool:
        """
        Check if the user is authenticated.
        Returns:
            True if the user is authenticated, False otherwise.
        """
        return self.login.authenticated() or self.orcid_auth.authenticated()


class SnapQuerySolution(InputWebSolution):
    """
    the Snap Query solution
    """

    def __init__(self, webserver: SnapQueryWebServer, client: Client):
        """
        Initialize the solution

        Calls the constructor of the base solution
        Args:
            webserver (SnapQueryWebServer): The webserver instance associated with this context.
            client (Client): The client instance this context is associated with.
        """
        super().__init__(webserver, client)  # Call to the superclass constructor
        self.webserver: SnapQueryWebServer
        self.authorization=self.webserver.authorization
        self.nqm = self.webserver.nqm
        self.endpoint_name = self.get_user_endpoint()

    def configure_settings(self):
        """
        add additional settings
        """
        self.add_select(
            "default Endpoint",
            list(self.nqm.endpoints.keys()),
            value=self.endpoint_name,
        ).bind_value(
            app.storage.user,
            "endpoint_name",
        )
        self.add_select(
            "prefix merger",
            {merger.name: merger.value for merger in QueryPrefixMerger},
            value=self.get_user_prefix_merger().name,
        ).bind_value(
            app.storage.user,
            "prefix_merger",
        )

    def setup_menu(self, detailed: bool = True):
        """
        setup the menu
        """
        ui.button(icon="menu", on_click=lambda: self.header.toggle())
        self.webserver: SnapQueryWebServer
        super().setup_menu(detailed=detailed)
        with self.header:
            self.header.value = False
            self.link_button("Nominate a Query", "/nominate", "post_add", new_tab=False)
            self.link_button(
                "Queries by Namespace",
                "/queries_by_namespace",
                "view_list",
                new_tab=False,
            )
            if self.webserver.authenticated():
                self.link_button("logout", "/logout", "logout", new_tab=False)
                if self.webserver.login.authenticated():
                    self.link_button("admin", "/admin", "supervisor_account", new_tab=False)
                self.link_button("stats", "/stats", icon_name="query_stats", new_tab=False)
            else:
                self.link_button("login", "/login", "login", new_tab=False)
                if self.webserver.orcid_auth.available():
                    redirect_url = self.webserver.orcid_auth.authenticate_url()
                    self.link_button("login with orcid", redirect_url, "login", new_tab=False)
            if self.webserver.orcid_auth.authenticated():
                orcid_token = self.webserver.orcid_auth.get_cached_user_access_token()
                # we have an ORCID authenticated user check the authorization
                self.user_has_llm_right = self.authorization.check_right_by_orcid(orcid_token.orcid, "LLM")
                checkmark = " LLM ✅" if self.user_has_llm_right else ""
                user_markup=f"*logged in as* **{orcid_token.name} ({orcid_token.orcid}) {checkmark}**"
                ui.markdown(user_markup).props(
                    "flat color=white icon=folder"
                ).classes("ml-auto")


    async def nominate_ui(self):
        """
        nominate a new query
        """

        def show():
            """
            show the nominate ui
            """

            def selection_callback(person: Person):
                self.container.clear()
                with self.container:
                    with ui.row().classes("w-full"):
                        with ui.column():
                            ui.label(text="Nominate your Query").classes("text-xl")
                            ui.link(
                                text="see the documentation for detailed information on the nomination procedure",
                                new_tab=True,
                                target="https://wiki.bitplan.com/index.php/Snapquery#nominate",
                            )
                        PersonView(person).classes("ml-auto bg-slate-100 rounded-md")
                with ui.row().classes("w-full"):
                    self.query_import_view = QueryImportView(self, allow_importing_from_url=False, person=person)

            with ui.column():
                ui.label(text="Nominate your Query").classes("text-xl")
                ui.link(
                    text="see the documentation for detailed information on the nomination procedure",
                    new_tab=True,
                    target="https://wiki.bitplan.com/index.php/Snapquery#nominate",
                )
                ui.label("Please identify yourself by entering or looking up a valid PID(Wikidata ID, ORCID, dblp).")
                self.person_selector = PersonSelector(solution=self, selection_callback=selection_callback)

        await self.setup_content_div(show)

    async def admin_ui(self):
        """
        admin ui
        """

        def show():
            """ """
            self.query_import_view = QueryImportView(self)

        await self.setup_content_div(show)

    async def login_ui(self):
        """
        login ui
        """
        await self.webserver.login.login(self)

    async def stats_ui(self):
        """
        stats ui
        """

        def show():
            """ """
            QueryStatsView(self)

        await self.setup_content_div(show)

    def setup_ui(self):
        """
        setup my user interface
        """
        self.search = NamedQuerySearch(self)

    async def home(
        self,
    ):
        """Generates the home page"""
        await self.setup_content_div(self.setup_ui)

    async def queries_by_namespace(self):
        def show():
            _nsv = NamespaceStatsView(self)

        await self.setup_content_div(show)

    async def query_page(
        self,
        domain: str,
        namespace: str,
        name: str,
        endpoint_name: str = "wikidata",
        limit: int = None,
        r_format_str: str = "html",
    ):
        def show():
            query_name = QueryName(domain=domain, namespace=namespace, name=name)
            qb = self.nqm.get_query(
                query_name=query_name,
                endpoint_name=endpoint_name,
                limit=limit,
                prefix_merger=self.get_user_prefix_merger(),
            )
            self.named_query_view = NamedQueryView(self, query_bundle=qb, r_format_str=r_format_str)

        await self.setup_content_div(show)

    @staticmethod
    def get_user_endpoint() -> str:
        """
        Get the endpoint selected by the user. If no endpoint is selected return the default endpoint wikidata
        """
        endpoint = app.storage.user.get("endpoint_name", "wikidata")
        return endpoint

    @staticmethod
    def get_user_prefix_merger() -> QueryPrefixMerger:
        """
        Get the prefix merger selected by the user. If no merger is selected the default merger Simple merger is used
        """
        merger_name = app.storage.user.get("prefix_merger", None)
        merger = QueryPrefixMerger.get_by_name(merger_name)
        if merger_name is None:
            app.storage.user["prefix_merger"] = merger.name
        return merger
