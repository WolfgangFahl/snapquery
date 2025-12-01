"""
Created on 29.06.2024
@author: wf
"""

import os
from dataclasses import field
from typing import Dict, List, Optional

from basemkit.yamlable import lod_storable


@lod_storable
class Endpoint:
    """
    A query endpoint for SPARQL, SQL or other storage systems
    """

    name: str
    endpoint: str
    lang: str = "sparql"
    website: Optional[str] = None
    database: Optional[str] = None
    method: Optional[str] = "POST"
    prefixes: Optional[str] = None
    auth: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None

    def __post_init__(self):
        """
        Perform post-initialization processing if needed.
        """
        pass

    @classmethod
    def get_samples(cls) -> dict[str, List["Endpoint"]]:
        """
        Get samples for Endpoint
        """
        samples = {
            "sample-endpoints": [
                cls(
                    name="wikidata",
                    lang="sparql",
                    endpoint="https://query.wikidata.org/sparql",
                    website="https://query.wikidata.org/",
                    database="blazegraph",
                    method="POST",
                    prefixes="PREFIX bd: <http://www.bigdata.com/rdf#>\nPREFIX cc: <http://creativecommons.org/ns#>",
                ),
                cls(
                    name="dbis-jena",
                    lang="sparql",
                    endpoint="https://confident.dbis.rwth-aachen.de/jena/",
                    website="https://confident.dbis.rwth-aachen.de",
                    auth="BASIC",
                    user="secret",
                    password="#not public - example not usable for access#",
                ),
            ]
        }
        return samples


@lod_storable
class EndpointManager:
    """
    Manages the storage and retrieval of
    Endpoint configurations.
    """

    endpoints: Dict[str, Endpoint] = field(default_factory=dict)

    @classmethod
    def get_yaml_path(cls) -> str:
        samples_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
        yaml_path = os.path.join(samples_path, "endpoints.yaml")
        return yaml_path

    def get_endpoint(self, name: str) -> Endpoint:
        """
        Retrieve an endpoint by name.
        """
        return self.endpoints.get(name)

    def __len__(self):
        return len(self.endpoints)

    def __iter__(self):
        return iter(self.endpoints.values())
