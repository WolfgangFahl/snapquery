"""
Created on 2025-12-04

@author: wf
"""

from argparse import ArgumentParser, Namespace
import sys

from basemkit.base_cmd import BaseCmd
from snapquery.qlever import QLever
from snapquery.query_set_tool import QuerySetTool
from snapquery.scholia import ScholiaQueries, GitHubQueries
from snapquery.sib_sparql_examples import SibSparqlExamples
from snapquery.snapquery_core import NamedQueryManager
from snapquery.version import Version
from snapquery.wd_page_query_extractor import WikidataQueryExtractor
from snapquery.wd_short_url import ShortUrl
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
            help="Enable LLM enrichment",
        )
        parser.add_argument(
            "--github",
            help="Extract queries from a specific GitHub repository (format: owner/repo).",
        )
        parser.add_argument(
            "--branch",
            help="GitHub branch or ref (optional for --github).",
        )
        parser.add_argument(
            "--github-path",
            default="",
            help="Sub-path within the GitHub repo to start valid extraction (default: root).",
        )

        parser.add_argument(
            "--github-extension",
            default=".rq",
            help="File extension to filter for when using --github (default: .rq).",
        )

        # Scholia options
        parser.add_argument(
            "--scholia",
            action="store_true",
            help="Run Scholia import (WDscholia/scholia) to generate a NamedQuerySet.",
        )
        parser.add_argument(
            "--scholia-qlever",
            action="store_true",
            help="Run Scholia QLever import (ad-freiburg/scholia/branch:qlever) to generate a NamedQuerySet.",
        )

        # Wikidata Examples options
        parser.add_argument(
            "--wikidata-examples",
            action="store_true",
            help="Extract official Wikidata SPARQL examples to generate a NamedQuerySet.",
        )
        # SIB options
        parser.add_argument(
            "--sib-examples",
            action="store_true",
            help="Extract SIB queries from GitHub to generate a NamedQuerySet.",
        )
        # QLever issues
        parser.add_argument(
            "--qlever-issues",
            action="store_true",
            help="Extract QLever Issues from GitHub to generate a NamedQuerySet.",
        )
        # Random short urls
        parser.add_argument(
            "--random-short-urls",
            action="store_true",
            help="Extract Random shorturls to generate  a NamedQuerySet.",
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

        if args.github:
            self._handle_github(args)
            return True

        if args.scholia:
            self._handle_scholia(args)
            return True

        if args.scholia_qlever:
            self._handle_scholia_qlever(args)
            return True

        if args.wikidata_examples:
            self._handle_wikidata_examples(args)
            return True

        if args.sib_examples:
            self._handle_sib_examples(args)
            return True

        if args.qlever_issues:
            self._handle_qlever_issues(args)
            return True

        if args.random_short_urls:
            self._handle_random_short_urls(args)
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
            short_urls=args.shorturl, domain=args.domain, namespace=args.namespace
        )

        self._output_dataset(nq_set, args)

    def _handle_github(self, args: Namespace) -> None:
        """
        Handle scraping a custom GitHub repository.
        """
        if "/" not in args.github:
            raise ValueError("GitHub argument must be in format 'owner/repo'")

        owner, repo = args.github.split("/", 1)

        nqm = NamedQueryManager.from_samples()

        gh_queries = GitHubQueries(
            nqm=nqm,
            owner=owner,
            repo=repo,
            branch=args.branch,
            path=args.github_path,
            extension=args.github_extension,
            domain=args.domain,
            namespace=args.namespace,
            debug=args.debug
        )

        gh_queries.extract_queries(limit=args.limit, show_progress=args.progress)
        self._output_dataset(gh_queries.named_query_set, args)


    def _handle_scholia(self, args: Namespace) -> None:
        """
        Handle the standard Scholia import workflow using defaults.
        """
        nqm = NamedQueryManager.from_samples()
        # Uses defaults defined in ScholiaQueries __init__
        scholia_queries = ScholiaQueries(nqm, debug=args.debug)
        scholia_queries.extract_queries(limit=args.limit, show_progress=args.progress)
        self._output_dataset(scholia_queries.named_query_set, args)

    def _handle_scholia_qlever(self, args: Namespace) -> None:
        """
        Handle the Scholia QLever import workflow using overridden parameters.
        """
        nqm = NamedQueryManager.from_samples()
        # Overrides for the QLever fork/branch
        scholia_qlever = ScholiaQueries(
            nqm=nqm,
            owner="ad-freiburg",
            repo="scholia",
            branch="qlever",
            namespace="named_queries_qlever",
            debug=args.debug
        )
        scholia_qlever.extract_queries(limit=args.limit, show_progress=args.progress)
        self._output_dataset(scholia_qlever.named_query_set, args)


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

    def _handle_sib_examples(self, args: Namespace) -> None:
        """
        Handle the Wikidata Examples import workflow.
        """
        debug = args.debug
        limit = args.limit
        show_progress = args.progress
        # Initialize NamedQueryManager
        nqm = NamedQueryManager.from_samples()
        sib_fetcher = SibSparqlExamples(nqm, debug=debug)
        if debug:
            print(f"Fetching SIB examples (limit={limit})...")
        _loaded_queries = sib_fetcher.extract_queries(limit=limit, debug_print=debug, show_progress=show_progress)
        self._output_dataset(sib_fetcher.named_query_set, args)

    def _handle_qlever_issues(self, args: Namespace):
        """
        Get QLever issues from GitHub and convert to NamedQuerySet.
        """
        # 1. Initialize logic class
        qlever = QLever(with_progress=args.progress, debug=args.debug)

        if args.debug or args.progress:
            print(f"Fetching QLever tickets from GitHub API (limit={args.limit})...")

        # 2. Execute extraction
        nq_set = qlever.get_issues_query_set(limit=args.limit, progress=args.progress)

        if args.debug:
            print(f"Extracted {len(nq_set.queries)} named queries.")

        # 3. Output result
        self._output_dataset(nq_set, args)

    def _handle_random_short_urls(self, args: Namespace) -> None:
        """
        Handle the random short URLs workflow.
        """
        # Set defaults for domain and namespace if not provided
        domain = args.domain if args.domain else "wikidata.org"
        namespace = args.namespace if args.namespace else "short_urls"

        # Determine count from limit or use default
        count = args.limit if args.limit else 100

        # Initialize NamedQueryManager
        nqm = NamedQueryManager.from_samples()

        if args.debug or args.progress:
            print(f"Extracting {count} random short URLs from Wikidata...")

        # Get random query set
        nq_set = ShortUrl.get_random_query_list(
            nqm=nqm,
            namespace=namespace,
            count=count,
            with_llm=args.llm,
            with_progress=args.progress,
            debug=args.debug,
        )

        if args.debug:
            print(f"Extracted {len(nq_set.queries)} random queries.")

        # Output the resulting NamedQuerySet
        self._output_dataset(nq_set, args)

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
