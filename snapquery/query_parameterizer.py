"""
Created on 2025-12-16

@author: wf
"""
import os
import re
import textwrap
from typing import Optional, Dict, Any, List

from lodstorage.params import Param
from lodstorage.query import Query
from snapquery.snapquery_core import NamedQuerySet, NamedQuery


class QueryParameterizer:
    """
    Parameterizer for Scholia Query Sets.
    Transforms Jinja2-based Scholia templates into standard
    LoDStorage Parameterized Queries.
    """

    # Replacement for Scholia's label macro
    LABEL_SERVICE = 'SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }'

    # Defaults for specific Scholia Aspects
    # derived from the prompt list
    ASPECT_DEFAULTS = {
        "author": "Q80",          # Tim Berners-Lee
        "authors": "Q80",
        "award": "Q616568",       # Turing Award
        "catalogue": "Q2463660",  # British Library catalogue
        "chemical": "Q18216",     # Aspirin
        "cito": "Q1054942",       # citation intent
        "clinical": "Q12136",     # Common Cold (disease context)
        "complex": "Q417724",     # Protein complex
        "countries": "Q183",      # Germany
        "country": "Q183",
        "dataset": "Q1172284",    # Data set
        "disease": "Q12136",      # Common Cold
        "event": "Q2020153",      # WWW Conference
        "gene": "Q7191",          # p53
        "index": "Q1",            # Universe (generic fallback)
        "language": "Q1860",      # English
        "lexeme": "Q151326",      # Word
        "license": "Q20007257",   # CC BY 4.0
        "location": "Q64",        # Berlin
        "ontology": "Q324254",    # Ontology
        "organization": "Q95",    # Google
        "organizations": "Q95",
        "pathway": "Q26487",      # Metabolic pathway
        "podcast": "Q24634210",   # The Ozymandias Project
        "printer": "Q11226",      # Printer (the device/person)
        "project": "Q5562725",    # WikiProject
        "property": "P31",        # Instance of
        "protein": "Q11060",      # Green fluorescent protein
        "publisher": "Q203019",   # Elsevier
        "retraction": "Q45263695", # Retracted paper example
        "series": "Q245209",      # Book series
        "software": "Q28865",     # Python
        "sponsor": "Q95",         # Google
        "taxon": "Q140",          # Lion
        "topic": "Q21198",        # Computer Science
        "topics": "Q21198",
        "use": "Q1",
        "uses": "Q1",
        "venue": "Q180445",       # Nature (Journal)
        "venues": "Q180445",
        "wikiproject": "Q5562725",
        "work": "Q13442814",      # Scientific Article
        "works": "Q13442814"
    }

    def __init__(self, debug: bool = False):
        self.debug = debug

    def _infer_param_details(self, var_name: str, aspect: Optional[str] = None) -> Dict[str, Any]:
        """
        Heuristics to determine type and default value based on variable name
        and the query aspect (category).

        Args:
            var_name: The variable name found in the jinja template (e.g. 'q', 'target').
            aspect: The scholia aspect derived from the query name (e.g. 'venue', 'author').
        """
        # Global Default
        details = {"type": "string", "default": "Q80"}

        # 1. Identify Type based on variable name
        if var_name in ['q', 'target', 'item', 'person', 'work', 'venue', 'gene', 'disease']:
            details["type"] = "WikidataItem"

            # 2. Assign Default Value based on Aspect
            if aspect and aspect in self.ASPECT_DEFAULTS:
                details["default"] = self.ASPECT_DEFAULTS[aspect]

            # 3. Fallback defaults if aspect is missing or generic
            elif var_name == 'person':
                details["default"] = "Q80"  # Tim Berners-Lee
            elif var_name == 'work':
                details["default"] = "Q13442814"
            else:
                details["default"] = "Q80"

        elif var_name in ['p', 'property']:
            details["type"] = "WikidataProperty"
            details["default"] = "P31"
        elif var_name in ['limit']:
            details["type"] = "int"
            details["default"] = 10
        elif var_name in ['lang', 'language']:
            details["type"] = "string"
            details["default"] = "en"

        return details

    def get_queries_by_aspect(self,query_list:List[Query])->Dict[str,List[Query]]:
        """
        get queries by aspect
        """
        queries_by_aspect = {}
        for query in query_list:
            aspect=self.get_aspect(query.name)
            if aspect in self.ASPECT_DEFAULTS:
                if aspect not in queries_by_aspect:
                    queries_by_aspect[aspect] = []
                queries_by_aspect[aspect].append(query)
        return queries_by_aspect

    def store_query_list(self,query_list:List[Query],tag:str,path:str="/tmp/queries"):
        """
        Store query list sorted by aspect into separate YAML files.

        Args:
            query_list (List[Query]): List of Query objects with aspect metadata.
            tag (str): Tag to include in filename.
            path (str): Directory path where YAML files will be stored.
        """
        queries_by_aspect=self.get_queries_by_aspect(query_list)
        # Create directory if it doesn't exist
        os.makedirs(path, exist_ok=True)

        # Store each aspect's queries in a separate YAML file
        for aspect, queries in sorted(queries_by_aspect.items()):
            filename = f"{tag}_{aspect}_queries.yaml"
            filepath = os.path.join(path, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                for query in queries:
                    # work around https://github.com/yaml/pyyaml/issues/411
                    if query.sparql:
                        clean_sparql = textwrap.dedent(query.sparql).strip()
                    yaml_str=query.to_yaml()
                    f.write(yaml_str)
            pass


    def parameterize_query_set(self, query_set: NamedQuerySet) -> List[Query]:
        """
        Parameterize the given query set to produce a list of LoDStorage queries.

        Args:
            query_set (NamedQuerySet): The set of named queries to transform.

        Returns:
            List[Query]: A list of transformed LoDStorage Query objects.
        """
        query_list = []
        for nq in query_set.queries:
            query = self.parameterize_query(nq)
            query_list.append(query)
        return query_list

    def get_aspect(self,name:str)->str:
        aspect = None
        if name:
            # Split by hyphen first, as that is the standard separator in the example
            parts = re.split(r'[-_]', name)
            if parts:
                aspect = parts[0].lower()
        return aspect

    def parameterize_query(self, nq: NamedQuery) -> Query:
        """
        Parameterize a single named query.

        1. Identifies the "Aspect" from the query name (e.g. 'venue-...' -> 'venue').
        2. Cleans Jinja2 specific imports.
        3. Replaces Scholia Macros with standard SPARQL.
        4. Detects variables and creates Param objects using aspect-specific defaults.

        Args:
            nq (NamedQuery): The named query input.

        Returns:
            Query: The transformed LoDStorage Query object.
        """
        # 0. Determine Aspect
        # Naming convention: {aspect}-{subname} or {aspect}_{subname}
        # e.g., "venue-curation_missing-author-item" -> "venue"
        aspect=self.get_aspect(nq.name)

        raw_sparql = nq.sparql

        # 1. Remove Jinja imports
        # e.g., {% import 'sparql-helpers.sparql' as sparql_helpers -%}
        txt = re.sub(r'\{%\s*import\s*.*?%\}', '', raw_sparql, flags=re.DOTALL)

        # 2. Replace Label/Description Macros
        # Matches: {{ sparql_helpers.labels(["?mol"], languages) }}
        txt = re.sub(
            r"\{\{\s*sparql_helpers\.(labels|descriptions).*?\}\}",
            self.LABEL_SERVICE,
            txt,
            flags=re.DOTALL
        )

        # 3. Detect Variables to build Param list
        found_vars = set(re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", txt))
        found_vars.discard('sparql_helpers')

        # Create lodstorage Query object
        clean_sparql = txt.strip()

        query_obj = Query(
            name=nq.name,
            query=clean_sparql,
            title=nq.title,
            description=nq.description,
            lang='sparql'
        )

        # 4. Attach Parameters with Aspect context
        param_list = []
        for var in sorted(found_vars):
            details = self._infer_param_details(var, aspect=aspect)
            p = Param(
                name=var,
                type=details["type"],
                default_value=details["default"]
            )
            param_list.append(p)

        query_obj.param_list = param_list

        return query_obj
