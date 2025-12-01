"""
Created on 2024-10-20

@author: wf
"""

from ngwidgets.basetest import Basetest

from snapquery.authorization import Authorization, UserRights


class TestAuthorization(Basetest):
    """
    test the Authorization
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_authorization(self):
        """
        Test the authorization
        """
        yaml_test_path = "/tmp/test_userrights.yaml"
        mock_rights = {"0000-0001-2345-6789": UserRights(name="John Doe", rights="llm")}
        auth = Authorization(user_rights=mock_rights)
        auth.save_to_yaml_file(yaml_test_path)
        auth_loaded = Authorization.load(yaml_test_path)
        result = auth_loaded.check_right_by_orcid("0000-0001-2345-6789", "llm")
        self.assertTrue(result)
