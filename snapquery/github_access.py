"""
GitHub API client for accessing repository contents.

Created on 2025-12-02
@author: wf
"""
import requests

class GitHub:
    """
    A simple GitHub API client for accessing repository contents.
    """

    def __init__(self, owner: str, repo: str, token: str = None):
        """
        Initialize GitHub client.

        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            token: Optional GitHub API token for authentication
        """
        self.owner = owner
        self.repo = repo
        self.token = token
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"

    def get_contents(self, path: str = ""):
        """
        Get contents of a directory or file from the repository.

        Args:
            path: Path within the repository

        Returns:
            List of dictionaries for directories, or content for files
        """
        url = f"{self.base_url}/contents/{path}"
        headers = {"Accept": "application/vnd.github.v3+json"}

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()