import logging
import random
import re
from collections import Counter
from typing import Iterable, Union

from jinja2 import Environment, Template, meta
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import CompValue

logger = logging.getLogger(__name__)


class SparqlAnalyzer:
    """
    SPARQL Query Analyzer
    """

    BLAZEGRAPH_NAMED_SUBQUERY_PATTERN = r"""WITH[\s\n]*(#[\w\s://\.\n,]+)?{(#[\w\s://\.\n,]+)?[\s\n](?P<subquery>[\n\r\b\w\d:\t\.";,\{\)\(\?\}\W#]*?)\s+[Aa][Ss]\s+%(?P<name>[A-Za-z\d_]+)"""

    @classmethod
    def get_prefix_luts(cls) -> dict[str, str]:
        return {
            "biopax": "http://www.biopax.org/release/biopax-level3.owl#",
            "bd": "http://www.bigdata.com/rdf#",
            "cc": "http://creativecommons.org/ns#",
            "datacite": "http://purl.org/spar/datacite/",
            "dblp": "https://dblp.org/rdf/schema#",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dct": "http://purl.org/dc/terms/",
            "freq": "http://purl.org/cld/freq/",
            "geo": "http://www.opengis.net/ont/geosparql#",
            "geof": "http://www.opengis.net/def/function/geosparql/",
            "geom": "http://geovocab.org/geometry#",
            "gpml": "http://vocabularies.wikipathways.org/gpml#",
            "litre": "http://purl.org/spar/literal/",
            "lgdo": "http://linkedgeodata.org/ontology/",
            "ontolex": "http://www.w3.org/ns/lemon/ontolex#",
            "orkgp": "http://orkg.org/orkg/predicate/",
            "orkgc": "http://orkg.org/orkg/class/",
            "orkgr": "http://orkg.org/orkg/resource/",
            "owl": "http://www.w3.org/2002/07/owl#",
            "p": "http://www.wikidata.org/prop/",
            "pav": "http://purl.org/pav/",
            "pq": "http://www.wikidata.org/prop/qualifier/",
            "pqn": "http://www.wikidata.org/prop/qualifier/value-normalized/",
            "pqv": "http://www.wikidata.org/prop/qualifier/value/",
            "pr": "http://www.wikidata.org/prop/reference/",
            "prn": "http://www.wikidata.org/prop/reference/value-normalized/",
            "prov": "http://www.w3.org/ns/prov#",
            "prv": "http://www.wikidata.org/prop/reference/value/",
            "ps": "http://www.wikidata.org/prop/statement/",
            "psn": "http://www.wikidata.org/prop/statement/value-normalized/",
            "psv": "http://www.wikidata.org/prop/statement/value/",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
            "schema": "http://schema.org/",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "void": "http://rdfs.org/ns/void#",
            "vrank": "http://purl.org/voc/vrank#",
            "wd": "http://www.wikidata.org/entity/",
            "wdata": "http://www.wikidata.org/wiki/Special:EntityData/",
            "wdno": "http://www.wikidata.org/prop/novalue/",
            "wdref": "http://www.wikidata.org/reference/",
            "wds": "http://www.wikidata.org/entity/statement/",
            "wdt": "http://www.wikidata.org/prop/direct/",
            "wdtn": "http://www.wikidata.org/prop/direct-normalized/",
            "wdv": "http://www.wikidata.org/value/",
            "wikibase": "http://wikiba.se/ontology#",
            "wp": "http://vocabularies.wikipathways.org/wp#",
            "wprdf": "http://rdf.wikipathways.org/",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "mwapi": "https://www.mediawiki.org/ontology#API/",
            "hint": "http://www.bigdata.com/queryHints#",
            "gas": "http://www.bigdata.com/rdf/gas#",
        }

    @classmethod
    def prefix_clause(cls, prefix: str, iri: str) -> str:
        """
        Provide SPARQL refix clause for given prefix and url
        Args:
            prefix: prefix name
            iri: iri

        Returns:
            prefix clause
        """
        return f"PREFIX {prefix}:  <{iri}>"

    @classmethod
    def extract_used_prefixes(cls, query: str) -> tuple[dict[str, str], set[str]]:
        """
        Extract used prefixes from SPARQL query
        Args:
            query: SPARQL query

        Returns:
            dict of declared prefixes
        """
        # add prefixes to avoid parsing error due to missing prefix
        prefix_lut = cls.get_prefix_luts()
        prefixed_query = cls._add_prefixes(prefix_lut, query)
        parsed_query = parseQuery(prefixed_query)
        elements = parsed_query.as_list()
        defined_prefixes = []
        used_prefixes = []
        for element in elements:
            if isinstance(element, CompValue) and element.name == "PrefixDecl":
                defined_prefixes.append(element)
            elif isinstance(element, CompValue) and element.name == "pname":
                used_prefixes.append(element)
            elif isinstance(element, Iterable) and not isinstance(element, str):
                if isinstance(element, dict):
                    elements.extend(element.values())
                else:
                    elements.extend(element)
            else:
                pass
        declared_prefix_counter = Counter(
            [value.get("prefix") for value in defined_prefixes]
        )
        multi_declarations = [
            prefix for prefix, count in declared_prefix_counter.items() if count > 1
        ]
        used_prefix_names = {value.get("prefix") for value in used_prefixes}
        used_prefix_map = dict()
        for prefix_value in reversed(defined_prefixes):
            prefix_name = prefix_value.get("prefix")
            prefix_iri = prefix_value.get("iri")
            if prefix_name in multi_declarations or prefix_name not in prefix_lut:
                used_prefix_map[prefix_name] = str(prefix_iri)
        return used_prefix_map, used_prefix_names

    @classmethod
    def add_missing_prefixes(cls, query: str):
        """
        Add missing prefixes to SPARQL query
        Args:
            query: SPARQL query

        Returns:
            SPARQL query
        """
        try:
            # normalize query for parsing
            prepared_query = query
            if cls.has_parameter(prepared_query):
                prepared_query = cls.fill_with_sample_query_parameters(prepared_query)
            if cls.has_blazegraph_with_clause(prepared_query):
                prepared_query = cls.transform_with_clause_to_subquery(prepared_query)
            # extract used and declared prefixes
            declared_prefixes, used_prefixes = cls.extract_used_prefixes(prepared_query)
            missing_prefix_declarations = used_prefixes - set(declared_prefixes.keys())
            undefined_prefixes = missing_prefix_declarations.difference(
                cls.get_prefix_luts().keys()
            )
            if undefined_prefixes:
                logger.error(
                    f"Prefix definitions missing for: {undefined_prefixes} → Not all prefixes that are missing can be added"
                )
            missing_prefix_declarations_lut = {
                key: value
                for key, value in cls.get_prefix_luts().items()
                if key in missing_prefix_declarations
            }
            fixed_query = cls._add_prefixes(missing_prefix_declarations_lut, query)
        except Exception as e:
            logger.debug(
                "Adding missing prefixes to query failed → Unable to parse SPARQL query"
            )
            logging.error(e)
            fixed_query = query
        return fixed_query

    @classmethod
    def transform_with_clause_to_subquery(cls, query: str) -> str:
        """
        Transform blazegraph with clause to subquery statement
        Args:
            query:

        Returns:

        """
        match = re.search(cls.BLAZEGRAPH_NAMED_SUBQUERY_PATTERN, query)
        if match:
            subquery = match.group("subquery")
            name = match.group("name")
            start_pos, end_pos = match.span()
            # check if Where mus be added
            select_part = query[:start_pos]
            where_part = query[end_pos + 1 :]
            if cls.has_blazegraph_with_clause(where_part):
                where_part = cls.transform_with_clause_to_subquery(where_part)
            if where_part.lower().strip().startswith("where"):
                query_with_removed = select_part + where_part
            else:
                query_with_removed = f"{select_part}\nWHERE\n{where_part}"

            include_pattern = f"[Ii][Nn][Cc][Ll][Uu][Dd][Ee]\s+%{name}"
            subquery = f"{{{subquery}\n"
            query_transformed = re.sub(include_pattern, subquery, query_with_removed)
            return query_transformed

    @classmethod
    def has_blazegraph_with_clause(cls, query: str) -> bool:
        """
        Check if the given query has a WITH clause (named subquery)
        For details see https://github.com/blazegraph/database/wiki/NamedSubquery
        Args:
            query: SPARQL query

        Returns:
            True if the query has a WITH clause (named subquery)
        """
        match = re.search(cls.BLAZEGRAPH_NAMED_SUBQUERY_PATTERN, query)
        return True if match else False

    @classmethod
    def _add_prefixes(cls, prefixes: dict[str, str], query: str) -> str:
        """
        Add prefixes to SPARQL query
        Args:
            prefixes: prefixes to add
            query: SPARQL query

        Returns:
            SPARQL query with prefixes added
        """
        prefixes_clauses = [
            cls.prefix_clause(prefix, iri) for prefix, iri in prefixes.items()
        ]
        prefixes_clauses_str = "\n".join(prefixes_clauses)
        return prefixes_clauses_str + "\n" + query

    @classmethod
    def has_parameter(cls, query: str) -> bool:
        """
        Check if the given query has parameters that need to need set
        Args:
            query: SPARQL query

        Returns:
            True if the query has parameters that need to need set
        """
        vars = cls.get_query_parameter(query)
        return len(vars) > 0

    @classmethod
    def get_query_parameter(cls, query: str) -> set[str]:
        env = Environment()
        ast = env.parse(query)
        vars = meta.find_undeclared_variables(ast)
        return vars

    @classmethod
    def fill_with_sample_query_parameters(cls, query: str) -> str:
        """
        Fill the given SPARQL query with sample query parameters
        Args:
            query: SPARQL query

        Returns:

        """
        if not cls.has_parameter(query):
            return query
        parameter_names = cls.get_query_parameter(query)
        params = cls._prepare_sample_parameter(parameter_names)
        return cls.bind_parameters_to_query(query, params)

    @classmethod
    def bind_parameters_to_query(cls, query: str, params: dict[str, str]) -> str:
        """
        Bind the parameters to the given query
        Args:
            query: SPARQL query
            params: quera params

        Returns:
            Query with parameters binded
        """
        template = Template(query)
        query_with_param_values = template.render(**params)
        return query_with_param_values

    @classmethod
    def _prepare_sample_parameter(cls, parameter_names: set[str]) -> dict[str, str]:
        """
        Prepare sample query parameters
        """
        params = dict()
        for name in parameter_names:
            params[name] = f"Q{random.randint(1, 1000)}"
        return params

    @classmethod
    def is_valid(cls, query: str):
        """
        Check if query is valid SPARQL query
        Args:
            query: SPARQL query

        Returns:
            True if query is valid SPARQL query
        """
        try:
            prepareQuery(query)
            return True
        except Exception as e:
            logger.debug(f"Query is not valid SPARQL query: {e}")
            return False

    def get_prefix_iri(self, prefix) -> Union[str, None]:
        return self.get_prefix_luts().get(prefix, None)
