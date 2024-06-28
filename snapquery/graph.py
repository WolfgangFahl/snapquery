"""
Created on 27.06.2024

@author: wf
"""
import os
from dataclasses import field
from typing import Dict

from lodstorage.yamlable import lod_storable


@lod_storable
class Graph:
    """
    A class representing a graph with its basic properties.
    """

    name: str
    default_endpoint_name: str
    description: str
    url: str
    comment: str = ""

    def __post_init__(self):
        """
        Perform post-initialization processing if needed.
        """
        pass

    @classmethod
    def get_samples(cls) -> dict[str, "Graph"]:
        """
        get samples for Graph
        """
        samples = {
            "graphs": [
                cls(
                    name="wikidata",
                    default_endpoint_name="wikidata",
                    description="Wikidata knowledge graph",
                    url="https://query.wikidata.org/sparql",
                    comment="Main Wikidata endpoint",
                ),
                cls(
                    name="dblp",
                    default_endpoint_name="dblp",
                    description="DBLP computer science bibliography",
                    url="https://qlever.cs.uni-freiburg.de/api/dblp",
                    comment="DBLP endpoint powered by QLever",
                ),
            ]
        }
        return samples


@lod_storable
class GraphManager:
    """
    Manages the storage and retrieval of
    Graph configurations.
    """

    graphs: Dict[str, Graph] = field(default_factory=dict)

    @classmethod
    def get_yaml_path(cls) -> str:
        samples_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "samples"
        )
        yaml_path = os.path.join(samples_path, "graphs.yaml")
        return yaml_path

    def get_graph(self, name: str) -> Graph:
        """
        Retrieve a graph by name.
        """
        return self.graphs.get(name)

    def __len__(self):
        return len(self.graphs)

    def __iter__(self):
        return iter(self.graphs.values())
