"""
Created on 2025-12-04

@author: wf
"""
from argparse import ArgumentParser, Namespace
import sys

from basemkit.base_cmd import BaseCmd
from snapquery.query_set_tool import QuerySetTool
from snapquery.scholia import ScholiaQueries
from snapquery.wd_page_query_extractor import WikidataQueryExtractor
from snapquery.snapquery_core import NamedQueryManager
from snapquery.version import Version
from tqdm import tqdm

class QuerySetCmdVersion(Version):
    """Version information"""
    name = "query-set"
    description = "QuerySet tool"

class QuerySetCmd(BaseCmd):
    """
    Command Line Interface for Query Set handling
    """

    def add_arguments(self, parser: ArgumentParser):
        """
        Add command-specific arguments.

        Args:
            parser: ArgumentParser to add arguments to
        """
        super().add_arguments(parser)
        # Conversion options
        parser.add_argument(
            "--convert",
            action="store_true",
            help="Convert a NamedQuerySet",
        )
        parser.add_argument(
            "-i",
            "--input",
            dest="input",
            help="Input file path or URL for a NamedQuerySet (JSON or YAML).",
        )
        parser.add_argument(
            "-o",
            "--output",
            dest="output",
            help="Output file path. If omitted, prints to stdout.",
        )
        parser.add_argument(
            "--in-format",
            choices=["auto", "json", "yaml"],
            default="auto",
            help="Input format. If 'auto', inferred from extension or tried JSON then YAML.",
        )
        parser.add_argument(
            "--out-format",
            choices=["yaml", "json"],
            default="yaml",
            help="Output format to write.",
        )
        parser.add_argument(
            "--indent",
            type=int,
            default=2,
            help="JSON pretty-print indentation for --out-format json.",
        )

        # Short URL path: create a NamedQuerySet from one or more w.wiki URLs
        parser.add_argument(
            "--shorturl",
            nargs="+",
            help="One or more Wikidata short URLs (e.g., https://w.wiki/XXXX) to build a NamedQuerySet.",
        )
        parser.add_argument(
            "--domain",
            help="Domain for NamedQuery(s) (required with --shorturl).",
        )
        parser.add_argument(
            "--namespace",
            help="Namespace for NamedQuery(s) (required with --shorturl).",
        )
        parser.add_argument(
            "--llm",
            action="store_true",
            help="Enable LLM enrichment (placeholder; not used in this snippet).",
        )
        # Scholia options
        parser.add_argument(
            "--scholia",
            action="store_true",
            help="Run Scholia import to generate a NamedQuerySet.",
        )
        # Wikidata Examples options
        parser.add_argument(
            "--wikidata-examples",
            action="store_true",
            help="Extract official Wikidata SPARQL examples to generate a NamedQuerySet.",
        )

        parser.add_argument(
            "--limit",
            type=int,
            help="Limit the number of queries extracted e.g. with --scholia",
        )
        parser.add_argument(
            "--progress",
            action="store_true",
            help="Show progress bar during execution.",
        )



    def handle_args(self, args: Namespace) -> bool:
        """
        Handle parsed arguments and execute scraping.

        Args:
            args: Parsed command-line arguments

        Returns:
            True if handled (no further processing needed)
        """
        handled = super().handle_args(args)
        if handled:
            return True

        if args.convert:
            self._handle_convert(args)
            return True

        # Short URL → NamedQuerySet
        if args.shorturl:
            self._handle_shorturl(args)
            return True

        if args.scholia:
            self._handle_scholia(args)
            return True

        if args.wikidata_examples:
            self._handle_wikidata_examples(args)
            return True


        return False

    def _handle_convert(self, args: Namespace) -> None:
        """
        Handle the conversion workflow delegating to QuerySetTool.
        """
        if not args.input:
            raise ValueError("Missing --input for --convert")

        tool = QuerySetTool()
        nq_set = tool.load_query_set(input_src=args.input, input_format=args.in_format)

        self._output_dataset(nq_set, args)

    def _handle_shorturl(self, args: Namespace) -> None:
        """
        Handle the short URL workflow delegating to QuerySetTool.
        """
        if not args.domain or not args.namespace:
            raise ValueError("--domain and --namespace are required with --shorturl")

        tool = QuerySetTool()
        nq_set = tool.get_query_set_from_short_urls(
            short_urls=args.shorturl,
            domain=args.domain,
            namespace=args.namespace
        )

        self._output_dataset(nq_set, args)

    def _handle_scholia(self, args: Namespace) -> None:
        """
        Handle the Scholia import workflow.
        """
        # Initialize NamedQueryManager (uses default/temporary DB as in samples)
        nqm = NamedQueryManager.from_samples()

        scholia_queries = ScholiaQueries(nqm, debug=args.debug)

        # Extract queries with limit and progress
        scholia_queries.extract_queries(limit=args.limit, show_progress=args.progress)

        # Output the resulting NamedQuerySet
        self._output_dataset(scholia_queries.named_query_set, args)

    def _handle_wikidata_examples(self, args: Namespace) -> None:
        """
        Handle the Wikidata Examples import workflow.
        """
        # Initialize NamedQueryManager
        nqm = NamedQueryManager.from_samples()

        # Configure extractor for official examples
        extractor = WikidataQueryExtractor(
            nqm=nqm,
            base_url="https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples",
            domain="wikidata.org",
            namespace="examples",
            target_graph_name="wikidata",
            debug=args.debug,
        )

        # 1. Fetch wikitext
        wikitext = extractor.fetch_wikitext()
        if not wikitext:
            return  # fetch_wikitext logs the error

        # 2. Parse sections
        sections = extractor.get_sections(wikitext)

        # 3. Iterate with optional progress
        iterator = sections
        if args.progress:
            print(f"Extracting queries from {extractor.base_url} ...")
            iterator = tqdm(sections)

        for section in iterator:
            extractor.extract_queries_from_section(section)

            # Simple approximation of limit based on queries stored
            if args.limit and len(extractor.named_query_list.queries) >= args.limit:
                break

        # Output the resulting NamedQuerySet
        self._output_dataset(extractor.named_query_list, args)


    def _output_dataset(self, nq_set, args: Namespace) -> None:
        """
        Helper to output a NamedQuerySet to file or stdout.
        """
        out_fmt = args.out_format
        if args.output:
            # Save to file
            if out_fmt == "yaml":
                nq_set.save_to_yaml_file(args.output)
            else:
                nq_set.save_to_json_file(args.output, indent=args.indent)
        else:
            # Print to stdout
            if out_fmt == "yaml":
                sys.stdout.write(nq_set.to_yaml(sort_keys=False))
            else:
                sys.stdout.write(nq_set.to_json(indent=args.indent))


def main(argv=None):
    """Main entry point."""
    exit_code = QuerySetCmd.main(QuerySetCmdVersion(), argv)
    return exit_code


if __name__ == "__main__":
    main()