"""
PID tests

@author wf
"""
import tempfile
from ngwidgets.basetest import Basetest
from snapquery.pid import PIDs
from snapquery.pid_lookup import PersonLookup
from snapquery.snapquery_core import NamedQueryManager

class TestPIDandPersons(Basetest):
    """
    Test cases for the PIDs and PersonLookup class.
    """
    
    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        tmpfile=tempfile.NamedTemporaryFile(delete=False)
        self.nqm = NamedQueryManager.from_samples(db_path=tmpfile.name)
    
    def test_person_lookup(self):
        """
        test person lookup
        """
        pl=PersonLookup(self.nqm)
        person_list=pl.suggest("Tim Bern")
        if self.debug:
            for i,person in enumerate(person_list):
                print(f"{i+1:2}:{person}")
                      
    def test_pids(self):
        """
        Tests the availability and validity of PIDs.
        """
        pids = PIDs()
        
        # Check that all expected PIDs are present
        assert "orcid" in pids.pids
        assert "dblp" in pids.pids
        assert "wikidata" in pids.pids
        
        # Check the attributes of each PID
        for key, pid in pids.pids.items():
            assert hasattr(pid, 'name')
            assert hasattr(pid, 'logo')
            assert hasattr(pid, 'formatter_url')
            assert hasattr(pid, 'regex')
            
            # Validate a sample value
            if key == "orcid":
                sample_value = "0000-0001-2345-6789"
            elif key == "dblp":
                sample_value = "m/xyz"
            elif key == "wikidata":
                sample_value = "Q42"
            
            pid_value = pids.pid4id(sample_value)
            assert pid_value is not None
            assert pid_value.is_valid()
            assert pid_value.url is not None
            assert pid_value.html is not None
