"""
Created on 2024-05-03

@author: wf
"""
import argparse
import logging
import sys
from argparse import ArgumentParser
from typing import Optional

from lodstorage.params import Params, StoreDictKeyPair
from lodstorage.query import Format
from ngwidgets.cmd import WebserverCmd

from snapquery.qimport import QueryImport
from snapquery.snapquery_core import NamedQuery, NamedQueryManager, QueryDetails
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
            help="Name of the endpoint to use for queries - use --listEndpoints to list available endpoints",
        )
        parser.add_argument(
            "-le",
            "--listEndpoints",
            action="store_true",
            help="show the list of available endpoints",
        )
        parser.add_argument(
            "-tq",
            "--testQueries",
            action="store_true",
            help="test run the queries",
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
        subparsers = parser.add_subparsers(help='sub-command help')
        snapquery_evaluate = subparsers.add_parser(name="evaluate" , description="evaluate queries by executing queries against different endpoints")
        snapquery_evaluate.set_defaults(func=self.snapquery_evaluate)
        snapquery_evaluate.add_argument("--namespaces", type=str, nargs="*" , default="wikidata-examples", help="evaluate all queries of the given namespace")
        snapquery_evaluate.add_argument("--context", type=str, default="test", help="context name to store the execution statistics with")
        snapquery_evaluate.add_argument( "--endpoints", type=str, nargs="*", default="wikidata",
                help="Name of the endpoint to use for queries - use --listEndpoints to list available endpoints", )
        snapquery_evaluate.add_argument( "-d", "--debug", action="store_true", help="Show debug messages")
        return parser

    def parameterize(self, nq: NamedQuery):
        """
        parameterize the given named query

        Args:
            nq(NamedQuery): the query to parameterize
        """
        qd = QueryDetails.from_sparql(query_id=nq.query_id, sparql=nq.sparql)
        # Execute the query
        params_dict = {}
        if qd.params == "q":
            # use Tim Berners-Lee as a example
            params_dict = {"q": "Q80"}
            pass
        return qd, params_dict

    def execute(self, nq: NamedQuery, endpoint_name: str, title: str, context: str):
        """
        execute the given named query
        """
        qd, params_dict = self.parameterize(nq)
        logger.debug(f"{title}: {nq.name} {qd} - via {endpoint_name}")
        _results, stats = self.nqm.execute_query(
            nq,
            params_dict=params_dict,
            endpoint_name=endpoint_name,
        )
        stats.context = context
        self.nqm.store_stats([stats])
        msg = f"{title} executed:"
        if not stats.records:
            msg += f"error {stats.filtered_msg}"
        else:
            msg += f"{stats.records} records found"
        logger.debug(msg)

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

    def setup_logger(self, level: int):
        """
        setup logging for the cmd
        """

    def snapquery_evaluate(self, args: argparse.Namespace):
        """
        Handle the evaluation of different endpoints by executing queries and storing the stats
        Args:
            args: argparse namespace
        """
        endpoint_names = args.endpoints
        namespaces = args.namespaces
        context = args.context
        self.nqm = NamedQueryManager.from_samples()
        if not endpoint_names:
            endpoint_names = list(self.nqm.endpoints.keys())
        # validate endpoint names
        skipped_namespaces = []
        for endpoint_name in endpoint_names:
            if endpoint_name not in self.nqm.endpoints:
                logger.error(f"Endpoint {endpoint_name} is not known and thus will be skipped")
                skipped_namespaces.append(endpoint_name)
        endpoint_names = [endpoint_name for endpoint_name in endpoint_names if endpoint_name not in skipped_namespaces]
        queries = []
        for namespace in namespaces:
            namespace_queries = self.nqm.get_all_queries(namespace=namespace)
            queries.extend(namespace_queries)
        for i, nq in enumerate(queries, start=1):
            for j, endpoint_name in enumerate(endpoint_names, start=1):
                logger.info(f"Executing query {i}/{len(queries)} ({i/len(queries):.2%}) on endpoint {endpoint_name} ({j}/{len(endpoint_names)})")
                self.execute(nq, endpoint_name=endpoint_name, title=f"query {i:3}/{len(queries)}::{endpoint_name}", context=context)

    def handle_args(self) -> bool:
        """
        handle the command line args
        """
        # Call the superclass handle_args to maintain base class behavior
        handled = super().handle_args()
        self.debug = self.args.debug
        nqm = NamedQueryManager.from_samples()
        self.nqm = nqm
        # Check if listing of endpoints is requested
        if self.args.listEndpoints:
            # List endpoints
            for endpoint in self.nqm.endpoints.values():
                print(endpoint)
            handled = True  # Operation handled
        elif self.args.testQueries:
            if self.args.endpointName:
                endpoint_names = [self.args.endpointName]
            else:
                endpoint_names = list(nqm.endpoints.keys())
            queries = self.nqm.get_all_queries(namespace=self.args.namespace)
            for i, nq in enumerate(queries, start=1):
                for endpoint_name in endpoint_names:
                    self.execute(
                        nq,
                        endpoint_name=endpoint_name,
                        title=f"query {i:3}/{len(queries)}::{endpoint_name}",
                    )
        elif self.args.queryName is not None:
            namespace = self.args.namespace
            name = self.args.queryName
            endpoint_name = self.args.endpointName
            r_format = self.args.format
            limit = self.args.limit
            qb = nqm.get_query(
                name=name, namespace=namespace, endpoint_name=endpoint_name, limit=limit
            )
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
        qimport = QueryImport(nqm=nqm)
        nq_list = qimport.import_from_json_file(
            json_file, with_store=True, show_progress=True
        )
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
