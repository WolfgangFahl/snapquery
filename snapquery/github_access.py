"""
GitHub API client for accessing repository contents.

Created on 2025-12-02
@author: wf
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests


class GitHub:
    """
    A simple GitHub API client for accessing repository contents.
    """

    def __init__(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        token: Optional[str] = None,
        session: Optional[requests.Session] = None
    ):
        """
        Initialize GitHub client.

        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            branch: Optional specific branch or commit SHA (default: default repo branch)
            token: Optional GitHub API token for authentication
            session: Optional custom requests.Session
        """
        self.owner = owner
        self.repo = repo
        self.branch = branch


        self.base_url = f"https://api.github.com/repos/{owner}/{repo}"

        # Use provided token or read from file
        self.token = token if token is not None else self._read_token()

        # Use custom session or create new one
        self.session = session or requests.Session()


    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _read_token(self) -> Optional[str]:
        """
        Read GitHub token from ~/.github/access_token.json
        (compatible with GitHubApi token storage format).

        Returns:
            GitHub token or None if not found
        """
        token_path = Path.home() / ".github" / "access_token.json"
        if token_path.exists():
            try:
                with open(token_path, "r") as f:
                    data = json.load(f)
                    return data.get("access_token")
            except (json.JSONDecodeError, OSError):
                pass
        return None

    def get_contents(self, path: str = "") -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get contents of a directory or file from the repository.

        Args:
            path: Path within the repository

        Returns:
            List of dictionaries for directories, or content for files
        """
        url = f"{self.base_url}/contents/{path}"
        params = {}
        if self.branch:
            params["ref"] = self.branch

        response = self.session.get(url, headers=self._headers(), params=params, timeout=30)
        response.raise_for_status()
        return response.json()


    def list_files_recursive(self, path: str = "", suffix: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recursively list files under a given path. Optionally filter by file suffix.

        Args:
            path: starting path within the repository
            suffix: optional filename suffix filter, e.g., ".ttl"

        Returns:
            A flat list of GitHub content item dicts for files.
        """
        items = self.get_contents(path)
        if isinstance(items, dict):
            items = [items]

        files: List[Dict[str, Any]] = []
        for item in items:
            item_type = item.get("type")
            item_path = item.get("path", "")
            if item_type == "file":
                if suffix is None or item_path.endswith(suffix):
                    files.append(item)
            elif item_type == "dir":
                files.extend(self.list_files_recursive(item_path, suffix=suffix))
        return files

    def download(self, download_url: str) -> str:
        """
        Download raw file content via a download_url.

        Args:
            download_url: The GitHub-provided raw download URL

        Returns:
            The text content of the file
        """
        response = self.session.get(download_url, headers=self._headers(), timeout=30)
        response.raise_for_status()
        return response.text
