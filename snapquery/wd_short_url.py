"""
Created on 2024-05-12

@author: wf
"""
import json
import random
import urllib.parse

import requests
from ngwidgets.llm import LLM

from snapquery.snapquery_core import NamedQuery, NamedQuerySet


class ShortIds:
    """
    short id handling
    """

    def __init__(
        self,
        base_chars: str = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz$",
    ):
        self.base_chars = base_chars

    def id_to_int(self, id_str: str) -> int:
        """
        Convert an ID string to an integer using my base character set.

        Args:
            id_str (str): The custom ID string to convert.

        Returns:
            int: The converted integer value.
        """
        base = len(self.base_chars)
        value = 0

        for char in id_str:
            value *= base
            value += self.base_chars.index(char)

        return value

    def get_random(self, k: int = 4) -> str:
        """
        get a random short id

        Returns:
            str: a random short id
        """
        short_id = "".join(random.choices(self.base_chars, k=k))
        return short_id


class ShortUrl:
    """
    Handles operations related to wikidata and similar short URLs such as QLever.
    see https://meta.wikimedia.org/wiki/Wikimedia_URL_Shortener for
    """

    def __init__(
        self, short_url: str, scheme: str = "https", netloc: str = "query.wikidata.org"
    ):
        """
        Constructor

        Args:
            short_url (str): The URL to be processed.
            scheme (str): URL scheme to be used (e.g., 'https' or 'http') for validating URL format.
            netloc (str): Network location part of the URL, typically the domain name, to be used for validating URL format.
        """
        self.short_url = short_url
        self.scheme = scheme
        self.netloc = netloc
        self.url = None
        self.sparql = None
        self.error = None

    @classmethod
    def get_prompt_text(cls, sparql: str) -> str:
        prompt_text = f"""give an english name, title and description in json 
for cut &paste for the SPARQL query below- the name should be less than 60 chars be a proper identifier which has no special chars so it can be used in an url without escaping. The title should be less than 80 chars and the 
description not more than three lines of 80 chars. 
A valid example result would be e.g.
{{
  "name": "Locations_in_Rennes_with_French_Wikipedia_Article"
  "title": "Locations in Rennes with a French Wikipedia Article",
  "description": "Maps locations in Rennes linked to French Wikipedia articles. It displays entities within 10 km of Rennes' center, showing their names, coordinates, and linked Wikipedia pages. The results include entities' identifiers, coordinates, and related site links."
}}

The example is just an example - do not use it's content if it does not match. 
Avoid  hallucinating and stick to the facts.
If the you can not determine a proper name, title and description return {{}}
SPARQL: {sparql}
"""
        return prompt_text

    @classmethod
    def get_random_query_list(
        cls,
        namespace: str,
        count: int,
        max_postfix="9pfu",
        with_llm=False,
        with_progress: bool = False,
        debug=False,
    ) -> NamedQuerySet:
        """
        Read a specified number of random queries from a list of short URLs.

        Args:
            namespace(str): the name to use for the named query list
            count (int): Number of random URLs to fetch.
            max_postfix(str): the maximum ID to try
            with_progress(bool): if True show progress

        Returns:
            NamedQueryList: A NamedQueryList containing the queries read from the URLs.
        """
        if with_llm:
            llm = LLM(model="gpt-4")
        short_ids = ShortIds()
        base_url = "https://w.wiki/"
        unique_urls = set()
        unique_names = set()

        nq_set = NamedQuerySet(
            domain="wikidata.org",
            namespace=namespace, 
            target_graph_name="wikidata")
        give_up = (
            count * 15
        )  # heuristic factor for probability that a short url points to a wikidata entry - 14 has worked so far
        max_short_int = short_ids.id_to_int(max_postfix)
        while len(unique_urls) < count and give_up > 0:
            if with_progress and not debug:
                print(".", end="")
                if give_up % 80 == 0:
                    print()
            # Generate a 4-char base36 string
            postfix = short_ids.get_random()
            if short_ids.id_to_int(postfix) > max_short_int:
                continue
            if debug:
                print(f"{give_up:4}:{postfix}")
            wd_short_url = f"{base_url}{postfix}"
            short_url = cls(short_url=wd_short_url)
            short_url.read_query()
            if short_url.sparql and not short_url.error:
                nq = NamedQuery(
                    domain=nq_set.domain,
                    name=postfix,
                    namespace=nq_set.namespace,
                    url=wd_short_url,
                    sparql=short_url.sparql,
                )
                if with_llm:
                    try:
                        llm_response = llm.ask(cls.get_prompt_text(short_url.sparql))
                        if llm_response:
                            response_json = json.loads(llm_response)
                            name = response_json.get("name", None)
                            if name in unique_names:
                                # try again with a different url to avoid name clash
                                give_up -= 1
                                continue
                            if name:
                                nq.name = name
                            title = response_json.get("title", "")
                            description = response_json.get("description", "")
                            nq.title = title
                            nq.description = description
                            nq.__post_init__()
                    except Exception as ex:
                        if debug:
                            print(f"Failed to get LLM response: {str(ex)}")
                        continue
                nq_set.queries.append(nq)
                unique_urls.add(nq.url)
                unique_names.add(nq.name)
                if debug:
                    print(nq)
            else:
                give_up -= 1
        return nq_set

    def fetch_final_url(self):
        """
        Follow the redirection to get the final URL.

        Returns:
            str: The final URL after redirection.
        """
        try:
            response = requests.get(self.short_url, allow_redirects=True)
            response.raise_for_status()
            self.url = response.url
        except Exception as ex:
            self.error = ex
        return self.url

    def read_query(self) -> str:
        """
        Read a query from a short URL.

        Returns:
            str: The SPARQL query extracted from the short URL.
        """
        self.fetch_final_url()
        if self.url:
            parsed_url = urllib.parse.urlparse(self.url)
            if parsed_url.scheme == self.scheme and parsed_url.netloc == self.netloc:
                if parsed_url.fragment:
                    self.sparql = urllib.parse.unquote(parsed_url.fragment)
                else:
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    if "query" in query_params:
                        self.sparql = query_params["query"][0]
        return self.sparql
