"""
Created on 2024-05-03

@author: wf
"""
import sys
from argparse import ArgumentParser

from ngwidgets.cmd import WebserverCmd

from snapquery.snapquery_webserver import SnapQueryWebServer


class SnapQueryCmd(WebserverCmd):
    """
    Command line for diagrams server
    """

    def getArgParser(self, description: str, version_msg) -> ArgumentParser:
        """
        override the default argparser call
        """
        parser = super().getArgParser(description, version_msg)
        return parser


def main(argv: list = None):
    """
    main call
    """
    cmd = SnapQueryCmd(
        config=SnapQueryWebServer.get_config(),
        webserver_cls=SnapQueryWebServer,
    )
    exit_code = cmd.cmd_main(argv)
    return exit_code


DEBUG = 0
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
