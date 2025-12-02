"""

SIB Swiss Institute of Bioinformatics

sparql examples

@author wf
"""
import unittest

from basemkit.basetest import Basetest
from rdflib import Graph


class TestSibExamples(Basetest):
    """
    Test for Issue #59
    https://github.com/WolfgangFahl/snapquery/issues/59
    https://github.com/sib-swiss/sparql-examples/

    Snap query should consider using the sparql-examples style of encoding queries as their own entities as the basis of it's data interchange
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)


    @unittest.skip("needs github clone to work -postpone")
    def testBgee(self):
        """
        test a single example
        """
        g= Graph().parse("examples/Bgee/001.ttl", format="turtle")
        query = g.value(None, g.namespace("sh")["select"])  # Gets sh:select literal
        print(query)  # Full SPARQL text