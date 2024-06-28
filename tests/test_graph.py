"""
Created on 2024-06-27

@author: wf
"""
from ngwidgets.basetest import Basetest

from snapquery.graph import Graph, GraphManager


class TestGraph(Basetest):
    """
    Test the Graph and GraphManager classes
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_graph_manager(self):
        """
        Test GraphManager functionality
        """
        manager=GraphManager()
        for name, graph_list in Graph.get_samples().items():
            for graph in graph_list:
                manager.graphs[graph.name]=graph
        yaml_path="/tmp/graphs.yaml" 
        manager.save_to_yaml_file(yaml_path)        
        yaml_path = GraphManager.get_yaml_path()
        manager = GraphManager.load_from_yaml_file(yaml_path)
        self.assertTrue("wikidata" in manager.graphs)
        for graph in manager:
            loaded_graph = manager.get_graph(graph.name)
            self.assertIsNotNone(loaded_graph)
            self.assertEqual(graph.name, loaded_graph.name)
            self.assertEqual(graph.url, loaded_graph.url)
