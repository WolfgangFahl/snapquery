from dataclasses import asdict, dataclass, fields
from pathlib import Path
from time import time
from typing import Optional, Union

import requests
from lodstorage.yamlable import lod_storable
from nicegui import app

from snapquery.models.person import Person


class OrcidAuth:
    """
    authenticate with orcid
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        config_file_name: str = "orcid_config.yaml",
    ):
        if base_path is None:
            base_path = Path.home() / ".solutions/snapquery"
        self.base_path = base_path
        self.config_file_name = config_file_name
        self.config = self.load_config()

    def get_config_path(self) -> Path:
        return self.base_path / self.config_file_name

    def config_exists(self):
        return self.get_config_path().exists()

    def available(self) -> bool:
        return self.config is not None

    def load_config(self) -> Union["OrcidConfig", None]:
        if not self.config_exists():
            return None
        config = OrcidConfig.load_from_yaml_file(str(self.get_config_path()))
        return config

    def authenticate_url(self):
        return self.config.authenticate_url()

    def authenticated(self) -> bool:
        authenticated = False
        if not self.available():
            return authenticated
        orcid_token = self.get_cached_user_access_token()
        if orcid_token is not None:
            authenticated = self._check_access_token(orcid_token)
        return authenticated

    def get_cached_user_access_token(self) -> Union["OrcidAccessToken", None]:
        orcid_token_record = app.storage.user.get("orcid_token", None)
        orcid_token = None
        if orcid_token_record:
            orcid_token: OrcidAccessToken = OrcidAccessToken.from_dict2(
                orcid_token_record
            )
        return orcid_token

    def _check_access_token(self, orcid_token: "OrcidAccessToken") -> bool:
        """
        Check if the given access token is valid
        Args:
            orcid_token: orcid access token

        Returns:
            True if the access token is valid, False otherwise
        """
        time_passed = int(time()) - orcid_token.login_timestamp
        if orcid_token.expires_in - time_passed < 0:
            return False
        else:
            return True

    def login(self, access_code: str) -> bool:
        authenticated = False
        try:
            orcid_token = self._retrieve_token(access_code)
            app.storage.user.update({"orcid_token": asdict(orcid_token)})
            authenticated = True
        except Exception as e:
            print(e)
            raise e
        return authenticated

    def _retrieve_token(self, code: str) -> "OrcidAccessToken":
        """
        URL=https://sandbox.orcid.org/oauth/token
         HEADER: Accept: application/json
         HEADER: Content-Type: application/x-www-form-urlencoded
         METHOD: POST
         DATA:
           client_id=[Your client ID]
           client_secret=[Your client secret]
           grant_type=authorization_code
           code=Six-digit code
           redirect_uri=[Your landing page]
        """
        url = f"{self.config.url}/oauth/token"
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "authorization_code",
            "code": code,
        }
        resp = requests.post(url, data=data)
        resp.raise_for_status()
        resp_json = resp.json()
        orcid_token: OrcidAccessToken = OrcidAccessToken.from_dict2(resp_json)
        return orcid_token

    def logout(self):
        """
        logout user by deleting cached access token
        """
        del app.storage.user["orcid_token"]

    def _request_search_token(self) -> str:
        """
        Request search token
        see https://info.orcid.org/documentation/api-tutorials/api-tutorial-searching-the-orcid-registry/

        URL=https://sandbox.orcid.org/oauth/token
          HEADER: Accept: application/json
          METHOD: POST
          DATA:
            client_id=[Your public API client ID]
            client_secret=[Your public API secret]
            grant_type=client_credentials
            scope=/read-public
        Returns:

        """
        url = f"{self.config.url}/oauth/token"
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "client_credentials",
            "scope": "/read-public",
        }
        resp = requests.post(url, data=data)
        resp.raise_for_status()
        resp_json = resp.json()
        return resp_json["access_token"]

    @property
    def search_token(self) -> str:
        if self.config.search_token is None:
            search_token = self._request_search_token()
            self.config.search_token = search_token
            self.store_config()
        return self.config.search_token

    def store_config(self):
        self.config.save_to_yaml_file(str(self.get_config_path()))

    def search(self, params: "OrcidSearchParams", limit: int = 10) -> list[Person]:
        access_token = self.search_token
        url = f"{self.config.api_endpoint}/expanded-search/?q={params.get_search_query()}&rows={limit}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        records: list[dict] = resp.json().get("expanded-result", [])
        persons = []
        if records:
            for record in records:
                person = Person(
                    given_name=record.get("given-names", None),
                    family_name=record.get("family-names", None),
                    orcid_id=record.get("orcid-id", None),
                )
                persons.append(person)
        return persons


@lod_storable
class OrcidConfig:
    """
    orcid authentication configuration
    """

    url: str
    client_id: str
    client_secret: str
    redirect_uri: str = "http://127.0.0.1:9862/orcid_callback"
    api_endpoint: str = "https://pub.orcid.org/v3.0"
    search_token: Optional[str] = None

    @classmethod
    def get_samples(cls) -> list["OrcidConfig"]:
        lod = [
            {
                "url": "https://orcid.org",
                "client_id": "APP-123456789ABCDEFG",
                "client_secret": "<KEY>",
                "redirect_uri": "http://127.0.0.1:9862/orcid_callback",
                "api_endpoint": "https://sandbox.orcid.org/v3.0",
            }
        ]
        return [OrcidConfig.from_dict2(d) for d in lod]

    def authenticate_url(self):
        return f"{self.url}/oauth/authorize?client_id={self.client_id}&response_type=code&scope=/authenticate&redirect_uri={self.redirect_uri}"


@lod_storable
class OrcidAccessToken:
    """
    orcid access token response
    """

    orcid: str
    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    scope: str
    name: str
    login_timestamp: int = int(time())

    @classmethod
    def get_samples(cls):
        lod = [
            {
                "access_token": "f5af9f51-07e6-4332-8f1a-c0c11c1e3728",
                "token_type": "bearer",
                "refresh_token": "f725f747-3a65-49f6-a231-3e8944ce464d",
                "expires_in": 631138518,
                "scope": "/activities/update /read-limited",
                "name": "Sofia Garcia",
                "orcid": "0000-0001-2345-6789",
            }
        ]
        return [OrcidAccessToken.from_dict2(d) for d in lod]


@dataclass
class OrcidSearchParams:
    """
    Orcid search api params
    see https://info.orcid.org/documentation/api-tutorials/api-tutorial-searching-the-orcid-registry/
    """

    # Biographical data
    given_names: Optional[str] = None
    family_name: Optional[str] = None
    credit_name: Optional[str] = None
    other_names: Optional[list[str]] = None
    email: Optional[str] = None
    keyword: Optional[list[str]] = None
    external_id_reference: Optional[str] = None

    # Affiliations data
    affiliation_org_name: Optional[str] = None
    grid_org_id: Optional[str] = None
    ror_org_id: Optional[str] = None
    ringgold_org_id: Optional[str] = None

    # Funding data
    funding_titles: Optional[list[str]] = None
    fundref_org_id: Optional[str] = None
    grant_numbers: Optional[list[str]] = None

    # Research activities data
    work_titles: Optional[list[str]] = None
    digital_object_ids: Optional[list[str]] = None

    # ORCID record data
    orcid: Optional[str] = None
    profile_submission_date: Optional[str] = None  # Assuming date format is string
    profile_last_modified_date: Optional[str] = None  # Assuming date format is string

    # All data (default for Lucene syntax)
    text: Optional[str] = None

    def get_search_query(self) -> str:
        query = ""
        dlim = ""
        for field in fields(self):
            key = field.name.replace("_", "-")
            value = getattr(self, field.name)
            if value is None:
                continue
            query += f"{key}:{value}"
            dlim = "+"
        return query
