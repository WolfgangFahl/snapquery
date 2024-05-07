"""
Created on 2024-05-03

@author: wf
"""

import sys
from argparse import ArgumentParser
from lodstorage.params import Params,StoreDictKeyPair
from lodstorage.query import EndpointManager, Format
from ngwidgets.cmd import WebserverCmd

from snapquery.qimport import QueryImport
from snapquery.snapquery_core import NamedQueryManager
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
        # see https://github.com/WolfgangFahl/pyLoDStorage/blob/master/lodstorage/querymain.py
        parser.add_argument(
            "-ep",
            "--endpointPath",
            default=None,
            help="path to yaml file to configure endpoints to use for queries",
        )
        parser.add_argument(
            "-en",
            "--endpointName",
            default="wikidata",
            help="Name of the endpoint to use for queries - use --listEndpoints to list available endpoints",
        )
        parser.add_argument(
            "-le",
            "--listEndpoints",
            action="store_true",
            help="show the list of available endpoints",
        )
        parser.add_argument(
            "--limit", type=int, default=None, help="set limit parameter of query"
        )
        parser.add_argument(
            "--params",
            action=StoreDictKeyPair,
            help="query parameters as Key-value pairs in the format key1=value1,key2=value2",
        )
        parser.add_argument(
            "--namespace",
            type=str,
            default="wikidata-examples",
            help="namespace to filter queries",
        )
        parser.add_argument("-f", "--format", type=Format, choices=list(Format))
        parser.add_argument("-qn", "--queryName", help="run a named query")
        parser.add_argument(
            "--import",
            dest="import_file",
            help="Import named queries from a JSON file.",
        )

        return parser

    def handle_args(self) -> bool:
        """
        handle the command line args
        """
        # Call the superclass handle_args to maintain base class behavior
        handled = super().handle_args()
        endpoints = EndpointManager.getEndpoints(self.args.endpointPath, lang="sparql")
        # Check if listing of endpoints is requested
        if self.args.listEndpoints:
            # List endpoints
            for endpoint in endpoints.values():
                print(endpoint)
            handled = True  # Operation handled
        elif self.args.queryName is not None:
            nqm = NamedQueryManager.from_samples()
            namespace = self.args.namespace
            name = self.args.queryName
            endpoint_name = self.args.endpointName
            r_format = self.args.format
            limit = self.args.limit
            qb = nqm.get_query(
                name=name, 
                namespace=namespace, 
                endpoint_name=endpoint_name, 
                limit=limit
            )
            query=qb.query
            params = Params(query.query)
            if params.has_params:
                if not self.args.params:
                    raise Exception(f"{query.name} needs parameters")
                else:
                    params.set(self.args.params)
                    query.query = params.apply_parameters()
            if r_format == Format.raw:
                formatted_result = qb.raw_query()
            else:
                qlod = qb.get_lod()
                formatted_result = qb.format_result(qlod=qlod, r_format=r_format)
            print(formatted_result)
        elif self.args.import_file:
            self.handle_import(self.args.import_file)
            handled = True
        return handled

    def handle_import(self, json_file: str):
        """
        Handle the import of named queries from a JSON file.

        Args:
            json_file (str): Path to the JSON file to import.
        """
        nqm = NamedQueryManager.from_samples()
        qimport = QueryImport(nqm=nqm)
        queries = qimport.import_from_json_file(
            json_file, with_store=True, show_progress=True
        )
        print(f"Imported {len(queries)} named queries from {json_file}.")


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
