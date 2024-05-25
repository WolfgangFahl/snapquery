"""
Created on 2024-05-12

@author: wf
"""
import unittest

from ngwidgets.basetest import Basetest

from snapquery.wd_short_url import ShortUrl


class TestShortUrl(Basetest):
    """
    test short url handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    @unittest.skipIf(Basetest.inPublicCI(), "unreliable execution in CI")
    def test_random_query_list(self):
        """
        test reading a random query list
        """
        if self.inPublicCI():
            with_llm = False
            count = 3
        else:
            count = 100
            with_llm = True
        nq_list = ShortUrl.get_random_query_list(
            name="short_urls", count=count, with_llm=with_llm, debug=self.debug
        )
        nq_list.save_to_json_file("/tmp/wikidata-short-urls.json", indent=2)
        self.assertEqual(count, len(nq_list.queries))
