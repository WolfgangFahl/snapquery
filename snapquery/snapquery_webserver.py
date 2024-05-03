"""
Created on 2024-05-03
@author: wf
"""
import asyncio
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from lodstorage.query import Query
from ngwidgets.input_webserver import InputWebserver, InputWebSolution, WebserverConfig
from nicegui import app
from nicegui.client import Client


from snapquery.snapquery_core import NamedQueryManager
from snapquery.version import Version
from snapquery.snapquery_view import NamedQuerySearch


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

        @app.get("/query/{namespace}/{name}", response_class=HTMLResponse)
        def query(namespace: str, name: str):
            """
            Executes a SPARQL query by name within a specified namespace, formats the results, and returns them as an HTML response.

            Args:
                namespace (str): The namespace identifying the group or category of the query.
                name (str): The specific name of the query to be executed.

            Returns:
                HTMLResponse: The HTML formatted response containing the results of the query execution.

            Raises:
                HTTPException: If the query cannot be found or fails to execute.
            """
            content=self.query(namespace,name)
            if not content:
                raise HTTPException(status_code=500, detail="Could not create result")

            # Return the content as an HTML response
            return HTMLResponse(content)
        
    def query(self,namespace:str,name:str):
        """
        """
        endpoint_name = "wikidata"
        # content negotiation
        # Determine response format by extension in the name or Accept header
        if '.' in name:
            r_format = name.split('.')[-1]
            name = name[:name.rfind('.')]
        else:
            r_format = "html"

        # Retrieve the SPARQL query string using the namespace and name.
        try:
            sparql_query = self.nqm.get_sparql(name, namespace, endpoint_name)
            qlod = self.nqm.query(
                name=name, namespace=namespace, endpoint_name=endpoint_name
            )
            query = Query(name=name, query=sparql_query, lang="sparql")
        except Exception as e:
            # Handling specific exceptions can be more detailed based on what nqm.get_sparql and nqm.query can raise
            raise HTTPException(status_code=404, detail=str(e))

        # Format the results and generate HTML content
        content = self.nqm.format_result(
            qlod, query, r_format, endpoint_name=endpoint_name
        )
        return content


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
        self.nqm=self.webserver.nqm
        self.endpoint_name="wikidata"
  
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
        self.search=NamedQuerySearch(self)
        
    async def home(
        self,
    ):
        """Generates the home page with a selection of examples and
        svg display
        """
        await self.setup_content_div(self.setup_ui)
