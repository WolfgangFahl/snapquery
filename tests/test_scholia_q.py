"""
Created on 2024-06-03

@author: wf
"""
import json
import unittest
from lodstorage.params import Params
from ngwidgets.basetest import Basetest
from snapquery.snapquery_core import NamedQueryManager
from ngwidgets.llm import LLM

class TestScholiaQ(Basetest):
    """
    test scholia q parameter handling
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.nqm = NamedQueryManager()

    @unittest.skipIf(Basetest.inPublicCI(), "avoid execution in CI due to LLM use")
    def testScholiaQParameterGuessing(self):
        """
        test guessing scholia Q Parameter guessing
        """
        limit=5
        llm = LLM(model="gpt-4o")
        namespace="scholia"
        records = self.nqm.sql_db.query(f"SELECT * FROM NamedQuery WHERE namespace='{namespace}'")
        for i,record in enumerate(records,start=1):
            name=record["name"]
            if self.debug:
                print (json.dumps(record,indent=2))
            sparql=record["sparql"]
            params = Params(sparql)
            if params.has_params:
                prompt=f""""What entity type should q be in the following SPARQL Query 
                and what would be a prominent example and the corresponding wikidata Identifier? The context is strictly scholarly publishing - make sure your choice fits this context. Never hallucinate wikidataIDs use None if you do not know 
                Answer in yaml format for cut&paste e.g. 
                entity:beer
                example:Heineken
                wikidataId:Q854383  
                
                SPARQL query to analyze: {sparql}"""
                try:
                    llm_response = llm.ask(prompt)
                    if llm_response:
                        print(llm_response)
                except Exception as ex:
                    print(f"guess {i} failed with exception {str(ex)}")
            if i>limit:
                break
                
                
                
  