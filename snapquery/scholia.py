"""
Created on 2024-05-04

@author: wf
"""
import requests

from snapquery.snapquery_core import NamedQueryManager


class ScholiaQueries:
    """
    scholia queries
    """

    @classmethod
    def get(cls, db_path: str = None, debug: bool = False, limit: int = None):
        nqm = NamedQueryManager.from_samples(db_path=db_path)
        repository_url = "https://api.github.com/repos/WDscholia/scholia/contents/scholia/app/templates"
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(repository_url, headers=headers)
        response.raise_for_status()  # Ensure we notice bad responses

        exclude = [
            "author_topics",
            "event_proceedings",
            "publisher_editors",
            "works_topics",
        ]
        lod = []
        file_list_json = response.json()
        for i, file_info in enumerate(file_list_json, start=1):
            file_name = file_info["name"]
            if file_name.endswith(".sparql") and file_name[:-7] not in exclude:
                file_response = requests.get(file_info["download_url"])
                file_response.raise_for_status()
                query_str = file_response.text
                name = file_name[:-7]
                record = {
                    "namespace": "scholia",
                    "name": name,
                    "url": file_info["download_url"],
                    "title": name,
                    "sparql": query_str,
                }
                lod.append(record)
                if debug:
                    if i % 80 == 0:
                        print(f"{i}")
                    print(".", end="", flush=True)
                if limit and len(lod) >= limit:
                    break
        if debug:
            print(f"found {len(lod)} scholia queries")
        nqm.store(lod)
        return nqm
