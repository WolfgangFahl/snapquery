"""
Created on 2024-05-04

@author: wf
"""

import json
import sys
from io import StringIO

from ngwidgets.basetest import Basetest

from snapquery import snapquery_cmd


class TestCommandLine(Basetest):
    """
    test the command line handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def capture_stdout(self, callback, *args, **kwargs):
        """
        Executes a callback with given arguments and captures stdout.
        """
        capture = StringIO()
        original_stdout = sys.stdout
        sys.stdout = capture
        try:
            callback(*args, **kwargs)
            return capture.getvalue()
        finally:
            sys.stdout = original_stdout

    def test_list_endpoints(self):
        """
        test listing endpoints

        """

        def run_cmd():
            snapquery_cmd.main(["--listEndpoints"])

        # Capture the output of running the command
        output = self.capture_stdout(run_cmd)
        if self.debug:
            print(output)
        self.assertTrue("wikidata:https://query.wikidata.org" in output)

    def test_namedquery(self):
        """
        test a named query via command line
        """
        limit = 10

        def run_cmd():
            snapquery_cmd.main(["-d", "-qn", "cats", "--limit", f"{limit}"])

        # Capture the output of running the command
        output = self.capture_stdout(run_cmd)
        if self.debug:
            print(output)
        # Parse the JSON output
        result = json.loads(output)
        # Check that the result has exactly 10 entries
        self.assertEqual(
            len(result), limit, "The number of results should be exactly 10."
        )

        # Check that each entry has 'item' and 'itemLabel'
        for entry in result:
            self.assertIn("item", entry, "Each entry must include an 'item'.")
            self.assertIn("itemLabel", entry, "Each entry must include an 'itemLabel'.")
