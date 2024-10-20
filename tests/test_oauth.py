"""
Created on 04.05.2024

@author: wf
"""

import webbrowser

from ngwidgets.basetest import Basetest

from snapquery.mwlogin import Login


class TestOAuthLogin(Basetest):
    """
    test login to mediawiki
    """

    def test_login(self):
        """
        test the login
        """
        if not self.inPublicCI():
            return
            print("Hint: Obtain the Consumer Key and Secret from your MediaWiki instance's OAuth management page.")
            url = "https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration"
            webbrowser.open(url)

            consumer_key = input("Enter Consumer Key: ")
            consumer_secret = input("Enter Consumer Secret: ")
            login = Login(consumer_key, consumer_secret)

            login.initiate_login()
            response_qs = input("Enter the response query string after authorization: ")
            login.complete_login(response_qs)

            if login.access_token:
                print("Login Successful!")
            else:
                print("Login Failed.")
