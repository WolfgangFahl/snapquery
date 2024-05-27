import tempfile
import unittest
from pathlib import Path
from ngwidgets.basetest import Basetest

from snapquery.models.person import Person
from snapquery.orcid import OrcidAuth, OrcidConfig, OrcidSearchParams


class TestOrcid(Basetest):
    """
    test OrcidAuth and OrcidConfig methods
    """

    def test_config_availability(self):
        """
        tests availability
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            basedir = Path(tmpdir) / ".solutions/snapquery"
            basedir.mkdir(exist_ok=True, parents=True)
            self.assertFalse(OrcidAuth(basedir).available())
            config = OrcidConfig.get_samples()[0]
            config_file_name = "orcid_config.yaml"
            config.save_to_yaml_file(basedir / config_file_name)
            orcid_auth = OrcidAuth(basedir, config_file_name)
            self.assertTrue(orcid_auth.available())
            authenticate_url = (
                "https://orcid.org/oauth/authorize?client_id=APP-123456789ABCDEFG&response_type=code&"
                "scope=/authenticate&redirect_uri=http://127.0.0.1:9862/orcid_callback"
            )
            self.assertEqual(orcid_auth.authenticate_url(), authenticate_url)

    @unittest.skipIf(not Path.home().joinpath(".solutions/snapquery").exists(), "Orcid configuration does not exist")
    def test_request_search_token(self):
        """
        test request search token
        """
        basedir = Path.home() / ".solutions/snapquery"
        orcid_auth = OrcidAuth(basedir)
        token = orcid_auth._request_search_token()
        res = orcid_auth.search(OrcidSearchParams(family_name="berners-lee"))
        self.assertIsInstance(res, list)
        for person in res:
            self.assertIsInstance(person, Person)
            self.assertIsNotNone(person.orcid_id)

