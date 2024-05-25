from dataclasses import dataclass
from typing import List, Optional
from sempubflow.models.affiliation import Affiliation

@dataclass
class Scholar:
    """
    a scholar
    """
    label: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    wikidata_id: Optional[str] = None
    dblp_author_id: Optional[str] = None
    orcid_id: Optional[str] = None
    image: Optional[str] = None
    affiliation: Optional[List[Affiliation]] = None
    official_website: Optional[str] = None
    
    @property
    def name(self) -> str:
        if not self.given_name and not self.family_name:
            return "❓"  # empty
        elif not self.given_name:
            return self.family_name
        elif not self.family_name:
            return self.given_name
        else:
            return f"{self.given_name} {self.family_name}"

    @property
    def ui_label(self) -> str:
        return self.name