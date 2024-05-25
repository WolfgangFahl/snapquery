import tempfile
import unittest
from pathlib import Path

from snapquery.orcid import OrcidAuth, OrcidConfig


class TestOrcid(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
