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
        nq_set = ShortUrl.get_random_query_list(
            name="wikidata.org/short_urls",
            count=count,
            with_llm=with_llm,
            debug=self.debug,
        )
        nq_set.save_to_json_file("/tmp/wikidata-short-urls.json", indent=2)
        self.assertEqual(count, len(nq_set.queries))
        
    @unittest.skipIf(Basetest.inPublicCI(), "unreliable execution in CI")
    def test_short_url(self):
        """
        test short url reading
        """
        for short_id in ["5aTp","5aHL","5b3r"]:
            short_url=ShortUrl(short_url=f"https://w.wiki/{short_id}")
            short_url.read_query()
            debug=self.debug
            debug=True
            if debug:
                print(short_url.sparql)
