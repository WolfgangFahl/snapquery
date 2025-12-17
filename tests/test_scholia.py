"""
Created on 2024-05-04

@author: wf
"""

import os
from pathlib import Path
import unittest
from basemkit.basetest import Basetest
from snapquery.scholia import ScholiaQueries, GitHubQueries
from snapquery.snapquery_core import NamedQueryManager, NamedQuerySet
from snapquery.query_parameterizer import QueryParameterizer

class TestScholia(Basetest):
    """
    test scholia queries
    """

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.samples_dir = Path(__file__).parent.parent / "snapquery" / "samples" / "query-sets" / "yaml"

    def prepare_nqm(self,prefix:str):
        self.prefix=prefix
        db_path = f"/tmp/{self.prefix}_queries.db"
        if os.path.exists(db_path):
            os.remove(db_path)
        # Adjust limit based on environment (e.g., CI)
        if self.inPublicCI():
            self.limit = 10
        else:
            self.limit = None
            # limit=10
        # Create a NamedQueryManager and ScholiaQueries instance
        self.nqm = NamedQueryManager.from_samples(db_path=db_path)

    def check_queries(self,queries,):
        queries.store_queries()
        queries.save_to_json(f"/tmp/{self.prefix}.json")

        # Verify the data was stored
        records = self.nqm.sql_db.query(
            f"""SELECT *
FROM NamedQuery
WHERE namespace='{queries.named_query_set.namespace}'
AND domain='{queries.named_query_set.domain}'
"""
        )
        self.assertEqual(len(records), len(queries.named_query_set.queries))


    @unittest.skipIf(Basetest.inPublicCI(), "avoid github rate limit")
    def test_scholia_queries(self):
        """
        Test retrieving Scholia queries.
        """
        prefix="scholia"
        nqm=self.prepare_nqm(prefix)
        scholia_queries = ScholiaQueries(nqm, debug=self.debug)

        # Extract, store, and save queries to JSON
        scholia_queries.extract_queries(limit=self.limit)
        self.check_queries(scholia_queries)

    @unittest.skipIf(Basetest.inPublicCI(), "avoid github rate limit")
    def test_scholia_qlever(self):
        """
        Test retrieving Scholia QLever queries from the specific branch.
        """
        prefix = "scholia_qlever"
        nqm = self.prepare_nqm(prefix)

        # Configure for ad-freiburg/scholia branch:qlever
        scholia_qlever = ScholiaQueries(
            nqm,
            owner="ad-freiburg",
            repo="scholia",
            branch="qlever",
            namespace="named_queries_qlever",
            debug=self.debug
        )

        scholia_qlever.extract_queries(limit=self.limit)
        self.check_queries(scholia_qlever)

    def test_parameterizing_queries(self):
        """
        test parameterizing scholia queries
        """
        debug=self.debug
        debug=True
        iso_date = "2025-12-16"
        parameterizer = QueryParameterizer(debug=debug)
        for tag in ["scholia","scholia-qlever"]:
            yaml_file=f"{tag}-{iso_date}.yaml"
            yaml_path = self.samples_dir / yaml_file
            query_set=NamedQuerySet.load_from_yaml_file(yaml_path) # @UndefinedVariable
            query_count=len(query_set.queries)
            if debug:
                print(f"Parameterizing {query_count} {tag} queries")
            pquery_list=parameterizer.parameterize_query_set(query_set)
            parameterizer.store_query_list(pquery_list, tag)
            self.assertEqual(len(pquery_list), query_count)
            if debug:
                for i,query in enumerate(pquery_list):
                    print(f"{i}:{query.to_yaml()}")

    @unittest.skipIf(Basetest.inPublicCI(), "avoid github rate limit")
    def test_exploratory_querying_sessions(self):
        owner = "hartig"
        repo= "ExploratoryQueryingSessions"
        path= "/sessions"
        extension = ".rq"
        limit = 5
        prefix="hartig_eqs"
        self.prepare_nqm(prefix)
        show_progress=self.debug
        show_progress=True
        hartig_queries = GitHubQueries(self.nqm, owner=owner,repo=repo, path=path,extension=extension, debug=self.debug)
        hartig_queries.extract_queries(limit=limit, show_progress=show_progress)
        self.check_queries(hartig_queries)

