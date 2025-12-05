"""
SIB SPARQL Examples Fetcher
Refactored to use a reusable GitHub API client and improved rdflib parsing.

Handles nested /examples/<service>/<NNN>.ttl structure.
Extracts sh:select, rdfs:comment, schema:target/labels as NamedQuery.
Exports to YAML (user request).

Modified: 2025-12-02 by wf
"""

import os
from typing import Any, Dict, List, Optional, Set

import rdflib
from tqdm import tqdm

from snapquery.github_access import GitHub
from snapquery.snapquery_core import NamedQuery, NamedQueryManager, NamedQuerySet


class SibSparqlExamples:
    """
    Fetch & parse SIB sparql-examples from GitHub API (remote, no clone).
    """

    def __init__(
        self,
        nqm: NamedQueryManager,
        github: Optional[GitHub] = None,
        debug: bool = False,
    ):
        self.nqm = nqm
        self.github = github or GitHub(owner="sib-swiss", repo="sparql-examples", token=os.getenv("GITHUB_TOKEN"))
        self.named_query_set = NamedQuerySet(
            domain="sparql-examples.sib.swiss",
            namespace="sib-examples",
            target_graph_name="various",  # varies per query (schema:target)
        )
        self.debug = debug
        self.cache: Dict[str, str] = {}  # TTL content cache
        self.stored_queries: List[NamedQuery] = []

    def collect_ttl_items(self, path: str = "examples") -> List[Dict[str, Any]]:
        """Recursively collect all .ttl file items under given path using GitHub client."""
        ttl_files = self.github.list_files_recursive(path, suffix=".ttl")
        return ttl_files

    def get_ttl_content(self, download_url: str) -> str:
        """Fetch TTL content from GitHub download_url, with cache."""
        if download_url in self.cache:
            return self.cache[download_url]
        content = self.github.download(download_url)
        self.cache[download_url] = content
        return content

    def get_html_url(self, file_path: str) -> str:
        """
        Construct GitHub HTML URL for a file path.

        Args:
            file_path: Path like "examples/Bgee/001.ttl"

        Returns:
            URL like "https://github.com/sib-swiss/sparql-examples/blob/main/examples/Bgee/001.ttl"
        """
        url = f"https://github.com/{self.github.owner}/{self.github.repo}/blob/main/{file_path}"
        return url

    def parse_ttl_to_namedqueries(self, ttl_content: str, ttl_path: str) -> List[NamedQuery]:
        """
        Parse TTL → NamedQuery using rdflib + SHACL shapes.
        Matches your Bgee sample exactly.
        """
        parsed_queries: List[NamedQuery] = []
        try:
            g = rdflib.Graph()
            g.parse(data=ttl_content, format="turtle")

            # path e.g. "examples/Bgee/001.ttl" → endpoint_path="Bgee/001"
            endpoint_path = ttl_path.replace("examples/", "").rstrip(".ttl")
            html_url = self.get_html_url(ttl_path)

            # Fixed SPARQL: direct sh:select on sh:SPARQLSelectExecutable (matches sample)
            qtext = """
            PREFIX sh: <http://www.w3.org/ns/shacl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX schema: <http://schema.org/>

            SELECT ?s ?query ?comment ?label WHERE {
              ?s a sh:SPARQLSelectExecutable ;
                 sh:select ?query .
              OPTIONAL { ?s rdfs:comment ?comment }
              OPTIONAL { ?s rdfs:label ?label }
              OPTIONAL { ?s schema:name ?label }  # Fallback label
            }
            """

            rows = list(g.query(qtext))
            if not rows:
                if self.debug:
                    print(f"No SHACL queries in {ttl_path}")
                return []

            seen_queries: Set[str] = set()
            fallback_title = endpoint_path.split("/")[-1].replace("_", " ").title()

            for i, row in enumerate(rows):
                query_str = str(row.query)
                if not query_str or query_str in seen_queries:
                    continue
                seen_queries.add(query_str)

                comment = str(row.comment) if row.comment else ""
                label = str(row.label) if row.label else fallback_title

                title = label
                description = comment or f"SIB example: {endpoint_path} ({title})"

                # Name: "Bgee:001" → slugify to "bgee-001"
                name_suffix = f"_{i+1}" if len(rows) > 1 else ""
                sub_name = endpoint_path.replace("/", ":") + name_suffix
                name = sub_name  # No duplicate prefix!

                base_url = f"https://sparql-examples.sib.swiss/{endpoint_path.replace('/', '/')}{name_suffix}"

                nq = NamedQuery(
                    domain=self.named_query_set.domain,
                    namespace=self.named_query_set.namespace,
                    name=name,
                    url=html_url,  # GitHub source
                    title=title,
                    description=description,
                    sparql=query_str,
                )
                parsed_queries.append(nq)

        except Exception as e:
            if self.debug:
                print(f"Error parsing {ttl_path}: {e}")
        return parsed_queries

    def extract_queries(
        self, limit: Optional[int] = None, debug_print: bool = False, show_progress: bool = False
    ) -> List[NamedQuery]:
        """
        Main: Fetch/parse/store all TTL → NamedQuery/DB/Set.
        """
        self.stored_queries.clear()
        ttl_items = self.collect_ttl_items("examples")
        if limit:
            ttl_items = ttl_items[:limit]

        iterator = ttl_items
        if show_progress:
            iterator = tqdm(ttl_items)

        for item in iterator:
            if debug_print:
                print(f"Processing {item['path']}...")
            content = self.get_ttl_content(item["download_url"])
            nqs = self.parse_ttl_to_namedqueries(content, item["path"])
            for nq in nqs:
                self.nqm.add_and_store(nq)  # FIXED: stores to DB + QueryDetails
                self.named_query_set.add(nq)  # FIXED: add (not add_query)
                self.stored_queries.append(nq)
        return self.stored_queries

    def save_to_yaml(self, filepath: str) -> Dict[str, Any]:
        """
        Export stored queries to a YAML file.
        """
        self.named_query_set.save_to_yaml_file(filepath)
