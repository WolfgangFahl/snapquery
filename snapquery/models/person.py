"""
Created 2023
refactored to snapquery by WF 2024-05

@author: th
"""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Affiliation:
    """
    affiliation of a person
    """
    name: Optional[str] = None
    location: Optional[str] = None
    country: Optional[str] = None
    wikidata_id: Optional[str] = None
    
    @property
    def ui_label(self) -> str:
        if not self.name:
            return "❓"  # empty
        else:
            return self.name

@dataclass
class PersonName:    
    """
    """    
    
    
    
        
@dataclass
class Person(PersonName):
    """
    A person
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
    
    @property
    def has_pid(self) -> bool:
        """
        Checks if the scholar has any persistent identifier (PID) set.
        """
        return any([self.wikidata_id, self.dblp_author_id, self.orcid_id])