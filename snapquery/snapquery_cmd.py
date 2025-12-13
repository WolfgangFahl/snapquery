"""
Created on 2024-05-03

@author: wf
"""

import logging
import sys
from argparse import ArgumentParser
from typing import Optional

from lodstorage.params import Params, StoreDictKeyPair
from lodstorage.query import Format
from ngwidgets.cmd import WebserverCmd
from tqdm import tqdm

from snapquery.execution import Execution
from snapquery.query_set_tool import QuerySetTool
from snapquery.snapquery_core import NamedQueryManager, QueryName, QueryPrefixMerger
from snapquery.snapquery_webserver import SnapQueryWebServer

logger = logging.getLogger(__name__)


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
            choices=list(NamedQueryManager.from_samples().endpoints.keys()),
            help="Name of the endpoint to use for queries - use --listEndpoints to list available endpoints",
        )
        parser.add_argument(
            "-idb",
            "--initDatabase",
            action="store_true",
            help="initialize the database",
        )
        parser.add_argument(
            "-le",
            "--listEndpoints",
            action="store_true",
            help="show the list of available endpoints",
        )
        parser.add_argument(
            "-lm",
            "--listMetaqueries",
            action="store_true",
            help="show the list of available metaqueries",
        )
        parser.add_argument(
            "-ln",
            "--listNamespaces",
            action="store_true",
            help="show the list of available namespaces",
        )
        parser.add_argument(
            "-lg",
            "--listGraphs",
            action="store_true",
            help="show the list of available graphs",
        )
        parser.add_argument(
            "-tq",
            "--testQueries",
            action="store_true",
            help="test run the queries",
        )
        parser.add_argument("--limit", type=int, default=None, help="set limit parameter of query")
        parser.add_argument(
            "--params",
            action=StoreDictKeyPair,
            help="query parameters as Key-value pairs in the format key1=value1,key2=value2",
        )
        parser.add_argument(
            "--progress",
            action="store_true",
            help="show progress bars when testing queries (--testQueries)",
        )

        parser.add_argument(
            "--domain",
            type=str,
            default="wikidata.org",
            help="domain to filter queries",
        )
        parser.add_argument(
            "--namespace",
            type=str,
            default="examples",
            help="namespace to filter queries",
        )
        parser.add_argument("-qn", "--queryName", help="run a named query")
        parser.add_argument(
            "query_id",
            nargs="?",  # Make it optional
            help="Query ID in the format 'name[--namespace[@domain]]'",
        )
        parser.add_argument("--format", type=Format, choices=list(Format))
        parser.add_argument(
            "--import",
            dest="import_file",
            help="Import named queries from a JSON file.",
        )
        parser.add_argument(
            "--github",
            type=str,
            help="GitHub repository to import queries from (in format 'owner/repo')",
        )

        parser.add_argument(
            "--context",
            type=str,
            default="test",
            help="context name to store the execution statistics with",
        )
        parser.add_argument(
            "--prefix_merger",
            type=str,
            default=QueryPrefixMerger.default_merger().name,
            choices=[merger.name for merger in QueryPrefixMerger],
            help="query prefix merger to use",
        )
        return parser

    def cmd_parse(self, argv: Optional[list] = None):
        """
        parse the argument lists and prepare

        Args:
            argv(list): list of command line arguments

        """
        super().cmd_parse(argv)
        if self.args.debug:
            level = logging.DEBUG
        else:
            level = logging.INFO
        logging.basicConfig(level=level)
        if hasattr(self.args, "func"):
            self.args.func(self.args)
        return self.args

    def handle_test_queries(self):
        """
        Handle the --testQueries option by executing queries against endpoints.
        The endpoint is the outer loop, queries are the inner loop.
        """
        # Determine which endpoints to use
        if self.args.endpointName:
            endpoint_names = [self.args.endpointName]
        else:
            endpoint_names = list(self.nqm.endpoints.keys())

        # Get all queries to test
        queries = self.nqm.get_all_queries(domain=self.args.domain, namespace=self.args.namespace)

        # Create execution instance
        execution = Execution(self.nqm, debug=self.args.debug)

        # Outer loop: endpoints
        endpoint_iter = tqdm(endpoint_names, desc="Testing endpoints") if self.args.progress else endpoint_names
        for endpoint_name in endpoint_iter:
            # Inner loop: queries
            query_iter = (
                tqdm(queries, desc=f"Queries for {endpoint_name}", leave=False) if self.args.progress else queries
            )
            for i, nq in enumerate(query_iter, start=1):
                execution.execute(
                    nq,
                    endpoint_name=endpoint_name,
                    context=self.args.context,
                    title=f"{endpoint_name}::query {i:3}/{len(queries)}",
                    prefix_merger=QueryPrefixMerger.get_by_name(self.args.prefix_merger),
                )

    def handle_test_queries_no_progress_version(self):
        if self.args.endpointName:
            endpoint_names = [self.args.endpointName]
        else:
            endpoint_names = list(self.nqm.endpoints.keys())
        queries = self.nqm.get_all_queries(domain=self.args.domain, namespace=self.args.namespace)
        execution = Execution(self.nqm, debug=self.args.debug)
        query_iter = tqdm(queries, desc="Testing queries") if self.args.progress else queries
        for i, nq in enumerate(query_iter, start=1):
            for endpoint_name in endpoint_names:
                execution.execute(
                    nq,
                    endpoint_name=endpoint_name,
                    context=self.args.context,
                    title=f"query {i:3}/{len(queries)}::{endpoint_name}",
                    prefix_merger=QueryPrefixMerger.get_by_name(self.args.prefix_merger),
                )

    def handle_args(self, args) -> bool:
        """
        handle the command line args
        """
        # Call the superclass handle_args to maintain base class behavior
        handled = super().handle_args(args)
        self.debug = self.args.debug
        nqm = NamedQueryManager.from_samples()
        self.nqm = nqm
        # Check args functions
        nqm = NamedQueryManager.from_samples(force_init=self.args.initDatabase)
        if self.args.listEndpoints:
            # List endpoints
            for endpoint in self.nqm.endpoints.values():
                print(endpoint)
            handled = True  # Operation handled
        elif self.args.listGraphs:
            print(self.nqm.gm.to_json(indent=2))
            handled = True
        elif self.args.listMetaqueries:
            meta_qm = self.nqm.meta_qm
            for name, query in meta_qm.queriesByName.items():
                print(f"{name}:{query.title}")
            handled = True
        elif self.args.listNamespaces:
            namespaces = self.nqm.get_namespaces()
            for namespace, count in namespaces.items():
                print(f"{namespace}:{count}")
            handled = True
        elif self.args.testQueries:
            self.handle_test_queries()
            handled = True
        elif self.args.queryName is not None or self.args.query_id is not None:
            if self.args.query_id is not None:
                query_name = QueryName.from_query_id(self.args.query_id)
            else:
                query_name = QueryName(
                    name=self.args.queryName,
                    namespace=self.args.namespace,
                    domain=self.args.domain,
                )
            endpoint_name = self.args.endpointName
            r_format = self.args.format
            limit = self.args.limit
            qb = nqm.get_query(query_name=query_name, endpoint_name=endpoint_name, limit=limit)
            query = qb.query
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
        qimport = QuerySetTool(nqm=nqm)
        nq_list = qimport.import_from_json_file(json_file, with_store=True, show_progress=True)
        print(f"Imported {len(nq_list.queries)} named queries from {json_file}.")


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
