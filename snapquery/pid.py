"""
Created on 2024-05-26
@author: wf
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class PID:
    """
    A persistent identifier source e.g. ORCID, dblpID or wikidata id
    """

    name: str
    logo: str
    formatter_url: str
    regex: str


@dataclass
class PIDValue:
    """
    Represents a specific instance of a persistent identifier with its value.
    """

    pid: PID
    value: str

    @property
    def url(self) -> str:
        return self.pid.formatter_url.format(self.value)

    @property
    def html(self) -> str:
        return f'<a href="{self.url}"><img src="{self.pid.logo}" alt="{self.pid.name} logo"> {self.value}</a>'

    def is_valid(self) -> bool:
        return re.match(self.pid.regex, self.value) is not None


class PIDs:
    """
    Available PIDs
    """

    def __init__(self):
        self.pids = {
            "orcid": PID(
                name="ORCID",
                logo="https://orcid.org/sites/default/files/images/orcid_16x16.png",
                formatter_url="https://orcid.org/{}",
                regex=r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$",
            ),
            "dblp": PID(
                name="dblp",
                logo="https://dblp.org/img/dblp-icon-64x64.png",
                formatter_url="https://dblp.org/pid/{}",
                regex=r"^[a-z0-9/]+$",
            ),
            "wikidata": PID(
                name="Wikidata",
                logo="https://www.wikidata.org/static/favicon/wikidata.ico",
                formatter_url="https://www.wikidata.org/wiki/{}",
                regex=r"^Q[0-9]+$",
            ),
        }

    def pid4id(self, identifier: str) -> Optional[PIDValue]:
        """
        Create a PIDValue instance based on the identifier type.
        """
        for _key, pid in self.pids.items():
            if re.match(pid.regex, identifier):
                return PIDValue(pid=pid, value=identifier)
        return None
