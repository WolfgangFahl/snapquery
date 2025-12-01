"""
Created on 20.10.2024

@author: wf
"""

import os
from dataclasses import field
from pathlib import Path

from basemkit.yamlable import lod_storable


@lod_storable
class UserRights:
    """
    the rights of a single user
    """

    name: str
    rights: str


@lod_storable
class Authorization:
    """
    Authorization check.
    """

    user_rights: dict[str, UserRights] = field(default_factory=dict)

    @classmethod
    def load(cls, yaml_path: str = None) -> "Authorization":
        """
        Load user rights from a YAML file, ensuring the file exists.
        """
        if yaml_path is None:
            yaml_path = os.path.expanduser("~/.openai/userrights.yaml")
        if not Path(yaml_path).exists():
            print(f"YAML file not found: {yaml_path}")
            return cls()

        return cls.load_from_yaml_file(yaml_path)

    def check_right_by_orcid(self, orcid: str, rights: str = None) -> bool:
        """
        Check if the user with the given ORCID has rights.
        Optionally checks for specific rights if provided.
        """
        user_right = self.user_rights.get(orcid)
        if user_right is None:
            return False
        ok = rights in user_right.rights
        return ok
