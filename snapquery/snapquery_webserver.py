"""
Created on 2024-05-03
@author: wf
"""

from fastapi import HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from lodstorage.query import Format
from ngwidgets.input_webserver import InputWebserver, InputWebSolution, WebserverConfig
from nicegui import app, ui
from nicegui.client import Client

from snapquery.snapquery_core import NamedQueryManager
from snapquery.snapquery_view import NamedQuerySearch, NamedQueryView
from snapquery.version import Version


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
        )
        server_config = WebserverConfig.get(config)
        server_config.solution_class = SnapQuerySolution
        return server_config

    def __init__(self):
        """Constructs all the necessary attributes for the WebServer object."""
        InputWebserver.__init__(self, config=SnapQueryWebServer.get_config())
        self.nqm = NamedQueryManager.from_samples()

        @ui.page("/query/{namespace}/{name}")
        async def query_page(
            client: Client,
            namespace: str,
            name: str,
            endpoint_name: str = "wikidata",
            limit: int = None,
            format: str = "html",
        ):
            """
            show the query page for the given namespace and name
            """
            return await self.page(
                client,
                SnapQuerySolution.query_page,
                namespace=namespace,
                name=name,
                endpoint_name=endpoint_name,
                limit=limit,
                r_format_str=format,
            )

        @app.get("/api/sparql/{namespace}/{name}")
        def sparql(
            namespace: str,
            name: str,
            endpoint_name: str = "wikidata",
            limit: int = None,
        ) -> PlainTextResponse:
            """
            Gets a SPARQL query by name within a specified namespace

            Args:
                namespace (str): The namespace identifying the group or category of the query.
                name (str): The specific name of the query to be executed.
                endpoint_name(str): the name of the endpoint to use
                limit(int): a limit to set, default=None
            Returns:
                HTMLResponse: The plain text SPARQL code

            Raises:
                HTTPException: If the query cannot be found or fails to execute.
            """
            qb = self.nqm.get_query(name, namespace, endpoint_name, limit)
            sparql_query = qb.query.query
            return PlainTextResponse(sparql_query)

        @app.get("/api/query/{namespace}/{name}")
        def query(
            namespace: str,
            name: str,
            endpoint_name: str = "wikidata",
            limit: int = None,
        ) -> HTMLResponse:
            """
            Executes a SPARQL query by name within a specified namespace, formats the results, and returns them as an HTML response.

            Args:
                namespace (str): The namespace identifying the group or category of the query.
                name (str): The specific name of the query to be executed.
                endpoint_name(str): the name of the endpoint to use
                limit(int): a limit to set, default=None

            Returns:
                HTMLResponse: The HTML formatted response containing the results of the query execution.

            Raises:
                HTTPException: If the query cannot be found or fails to execute.
            """
            content = self.query(
                namespace, name, endpoint_name=endpoint_name, limit=limit
            )
            if not content:
                raise HTTPException(status_code=500, detail="Could not create result")

            # Return the content as an HTML response
            return HTMLResponse(content)

    def query(
        self,
        namespace: str,
        name: str,
        endpoint_name: str = "wikidata",
        limit: int = None,
    ) -> str:
        """
        Queries an external API to retrieve data based on a given namespace and name.

        Args:
            namespace (str): The namespace to which the query belongs. It helps in categorizing the data.
            name (str): The name identifier of the data to be queried.
            endpoint_name (str): The name of the endpoint to be used for the query. Defaults to 'wikidata'.
            limit(int): the limit for the query default: None

            Returns:
                str: the content retrieved
        """
        # content negotiation
        # Determine response format by extension in the name or Accept header
        if "." in name:
            r_format_str = name.split(".")[-1]
            name = name[: name.rfind(".")]
        else:
            r_format_str = "html"

        try:
            r_format = Format[r_format_str]
            qb = self.nqm.get_query(name, namespace, endpoint_name, limit)
            qlod = qb.get_lod()
            content = qb.format_result(qlod, r_format)
            return content
        except Exception as e:
            # Handling specific exceptions can be more detailed based on what nqm.get_sparql and nqm.query can raise
            raise HTTPException(status_code=404, detail=str(e))


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
        self.nqm = self.webserver.nqm
        self.endpoint_name = "wikidata"

    def configure_settings(self):
        """
        add additional settings
        """
        self.add_select("default Endpoint", list(self.nqm.endpoints.keys())).bind_value(
            self, "endpoint_name"
        )

    def setup_ui(self):
        """
        setup my user interface
        """
        self.search = NamedQuerySearch(self)

    async def home(
        self,
    ):
        """Generates the home page with a selection of examples and
        svg display
        """
        await self.setup_content_div(self.setup_ui)

    async def query_page(
        self,
        namespace: str,
        name: str,
        endpoint_name: str = "wikidata",
        limit: int = None,
        r_format_str: str = "html",
    ):
        def show():
            query_bundle = self.nqm.get_query(name, namespace, endpoint_name, limit)
            self.named_query_view = NamedQueryView(
                self, query_bundle=query_bundle, r_format_str=r_format_str
            )

        await self.setup_content_div(show)
