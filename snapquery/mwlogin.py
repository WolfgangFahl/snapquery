"""
Created on 04.05.2024

@author: wf
"""
# mwlogin.py

import webbrowser

from mwoauth import ConsumerToken, Handshaker


class Login:
    """
    login to mediawiki
    """

    def __init__(
        self,
        consumer_key,
        consumer_secret,
        wiki_url="https://en.wikipedia.org/w/index.php",
    ):
        self.consumer_token = ConsumerToken(consumer_key, consumer_secret)
        self.handshaker = Handshaker(wiki_url, self.consumer_token)
        self.request_token = None
        self.access_token = None

    def initiate_login(self):
        """
        Step 1: Initialize -- ask MediaWiki for a temporary key/secret for user
        """
        redirect, self.request_token = self.handshaker.initiate()
        webbrowser.open(redirect)
        print(
            "Browser opened to MediaWiki login page. Please authorize the application."
        )

    def complete_login(self, response_qs):
        """
        Step 3: Complete -- obtain authorized key/secret for "resource owner"
        """
        self.access_token = self.handshaker.complete(self.request_token, response_qs)
        print("Login completed successfully.")

    def identify_user(self):
        """
        Step 4: Identify -- (optional) get identifying information about the user
        """
        if self.access_token:
            identity = self.handshaker.identify(self.access_token)
            print(f"Identified as {identity['username']}.")
        else:
            print(
                "Access token is not available. Please complete the login process first."
            )
