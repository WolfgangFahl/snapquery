"""
Created on 2024-05-05

@author: wf
"""

import glob
import os
from typing import List, Optional

from tqdm import tqdm

from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet
from snapquery.wd_short_url import ShortUrl


class QuerySetTool:
    """
    Tool to:
     - import named queries from a given URL or file.
     - convert file formats for loading and storing
     - process short URLs
    """

    def __init__(self, nqm: NamedQueryManager = None):
        """
        Constructor

        Args:
            nqm (NamedQueryManager, optional): The NamedQueryManager to use for storing queries.
        """
        self.nqm = nqm

    def infer_format(self, source: str, input_format: str = "auto") -> str:
        """
        Infer input format by flag or extension, fallback to auto.

        Args:
            source (str): The filename or URL.
            input_format (str): The format hint ('auto', 'json', 'yaml').

        Returns:
            str: The inferred format.
        """
        if input_format != "auto":
            return input_format

        # Try to infer from file extension
        src_lower = source.lower() if source else ""
        if src_lower.endswith((".yaml", ".yml")):
            return "yaml"
        if src_lower.endswith(".json"):
            return "json"

        # Unknown: return auto to let loader try everything
        return "auto"

    def load_query_set(self, input_src: str, input_format: str = "auto") -> NamedQuerySet:
        """
        Load a NamedQuerySet from a file or URL, implementing format inference.

        Args:
            input_src (str): File path or URL.
            input_format (str): 'auto', 'json', or 'yaml'.

        Returns:
            NamedQuerySet: The loaded object.
        """
        fmt = self.infer_format(input_src, input_format)
        is_url = input_src.startswith(("http://", "https://")) if input_src else False

        result = None

        if is_url:
            if fmt == "json":
                result = NamedQuerySet.load_from_json_url(input_src)  # @UndefinedVariable
            elif fmt == "yaml":
                result = NamedQuerySet.load_from_yaml_url(input_src)  # @UndefinedVariable
            else:
                # auto: try JSON, then YAML
                try:
                    result = NamedQuerySet.load_from_json_url(input_src)  # @UndefinedVariable
                except Exception:
                    result = NamedQuerySet.load_from_yaml_url(input_src)  # @UndefinedVariable
        else:
            if fmt == "json":
                result = NamedQuerySet.load_from_json_file(input_src)  # @UndefinedVariable
            elif fmt == "yaml":
                result = NamedQuerySet.load_from_yaml_file(input_src)  # @UndefinedVariable
            else:
                # auto: try JSON, then YAML
                try:
                    result = NamedQuerySet.load_from_json_file(input_src)  # @UndefinedVariable
                except Exception:
                    result = NamedQuerySet.load_from_yaml_file(input_src)  # @UndefinedVariable

        return result

    def get_query_set_from_short_urls(
        self, short_urls: List[str], domain: str, namespace: str, target_graph_name: str = "wikidata"
    ) -> NamedQuerySet:
        """
        Fetch multiple short URLs and aggregate them into a NamedQuerySet.

        Args:
            short_urls (List[str]): List of w.wiki URLs.
            domain (str): Domain for the NamedQuerySet (and NamedQueries).
            namespace (str): Namespace for the NamedQuerySet (and NamedQueries).
            target_graph_name (str): Target graph name.

        Returns:
            NamedQuerySet: The resulting set.
        """
        queries = []
        for url in short_urls:
            su = ShortUrl(url)
            nq = self.read_from_short_url(short_url=su, domain=domain, namespace=namespace)
            if nq is None:
                raise ValueError(f"Failed to fetch/parse short URL: {url}")
            queries.append(nq)

        nq_set = NamedQuerySet(domain=domain, namespace=namespace, target_graph_name=target_graph_name, queries=queries)
        return nq_set

    def import_samples(self, with_store: bool = True, show_progress: bool = False):
        """
        import all sample json files

        Args:
            with_store(bool): if True store the result
            show_progress(bool): if True show a tqdm progress bar
        """
        for json_file in glob.glob(os.path.join(self.nqm.samples_path, "*.json")):
            try:
                nq_list = self.import_from_json_file(json_file, with_store, show_progress)
            except Exception as ex:
                print(f"could not load json_file {json_file}")
                raise ex
            if "ceur" in json_file:
                json_file_name = os.path.basename(json_file)
                output_path = os.path.join("/tmp", json_file_name)
                nq_list.save_to_json_file(output_path, indent=2)
                pass

    def import_from_json_file(
        self, json_file: str, with_store: bool = False, show_progress: bool = False
    ) -> NamedQuerySet:
        """
        Import named queries from a JSON file.

        Args:
            json_file (str): Path to the JSON file.
            with_store (bool): If True, store the results in the NamedQueryManager.
            show_progress (bool): If True, show a progress bar during the import.

        Returns:
            NamedQuerySet: A NamedQuerySet object containing the imported NamedQuery objects.
        """
        nq_set = NamedQuerySet.load_from_json_file(json_file)  # @UndefinedVariable
        iterable = (
            tqdm(
                nq_set.queries,
                desc=f"Importing Namespace {nq_set.namespace}@{nq_set.domain}",
            )
            if show_progress
            else nq_set.queries
        )

        for nq in iterable:
            if not nq.sparql:
                if nq.url and nq.url.startswith("https://w.wiki/"):
                    short_url = ShortUrl(nq.url)
                    nq.sparql = short_url.read_query()
                else:
                    raise Exception(f"invalid named query with no url: {nq}")
                    # what now?
                    continue
            if with_store and self.nqm:
                self.nqm.add_and_store(nq)
        return nq_set

    def read_from_short_url(
        self,
        short_url: ShortUrl,
        domain: str,
        namespace: str,
    ) -> Optional[NamedQuery]:
        """
        Read and process a single short URL, optionally enriching it with LLM-generated metadata.

        Args:
            short_url (ShortUrl): The ShortUrl instance to process
            domain (str): the domain for the named query
            namespace (str): the namespace for the named query

        Returns:
            NamedQuery | None: A NamedQuery object if successful, None if processing fails
        """
        short_url.read_query()
        if not short_url.sparql or short_url.error:
            return None

        nq = NamedQuery(
            domain=domain,
            name=short_url.name,
            namespace=namespace,
            url=short_url.short_url,
            sparql=short_url.sparql,
        )
        return nq
