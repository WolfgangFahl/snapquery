'''
Created on 2024-05-03
@author: wf
'''
from nicegui.client import Client
from ngwidgets.input_webserver import InputWebserver, InputWebSolution, WebserverConfig
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
        InputWebserver.__init__(
            self, config=SnapQueryWebServer.get_config()
        )
        
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