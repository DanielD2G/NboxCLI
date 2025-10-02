import requests

from nbox_cli.config import load_config

config = load_config()
API_URL = config.nbox_url


class NboxRequestClient:
    def __init__(self, token=None) -> None:
        self._client = requests.Session()
        self._bearer_token = token or config.nbox_token
        self._entry_client = None

        if not self._bearer_token:
            raise Exception("No authentication token found. Please run 'nbox login' first.")

        self._client.headers.update(
            {"Authorization": f"Bearer {self._bearer_token}"}
        )

    def validate_token(self):
        url = API_URL + "/api/entry/" + "prefix"
        params = {"v": 'login'}
        response = self._client.get(url, params=params)
        if response.status_code == 200:
            result = response.json()
            return result
        else:
            raise Exception(
                f"Request failed with status {response.status_code}: {response.text}"
            )

    @property
    def entry(self):
        if not self._entry_client:
            self._entry_client = NboxEntryClient(self)

        return self._entry_client

    @staticmethod
    def login(username: str, password: str):
        url = API_URL + "/api/auth/token"
        payload = {"username": username, "password": password}
        client = requests.Session()
        response = client.post(url, json=payload)

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token")

            config.nbox_token = token
            config.save()

            return token
        else:
            raise Exception(
                f"Login failed with status {response.status_code}: {response.text}"
            )


class NboxEntryClient:
    BASE_URL = API_URL + "/api/entry/"

    def __init__(self, nbox_request_client=None) -> None:
        self.nbox_request_client = nbox_request_client or NboxRequestClient()
        if not self.nbox_request_client._bearer_token:
            raise Exception("Cannot use clients without authentication")
        self._client = self.nbox_request_client._client

    def get_entries_by_prefix(self, path, decrypt=False):
        url = self.BASE_URL + "prefix"
        params = {"v": path}
        response = self._client.get(url, params=params)

        if response.status_code == 200:
            result = response.json()

            if decrypt:
                for entry in result:
                    if entry.get('secure', False):
                        try:
                            secret_value = self.get_secret_by_key(entry['value'])
                            entry['value'] = secret_value["value"]
                        except Exception as e:
                            entry['decryption_error'] = str(e)

            return result
        else:
            raise Exception(
                f"Request failed with status {response.status_code}: {response.text}"
            )

    def get_entry_by_key(self, key: str):
        url = self.BASE_URL + "key"
        key = key.lstrip("/")
        params = {"v": key}
        response = self._client.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Request failed with status {response.status_code}: {response.text}"
            )

    def delete_entry_by_key(self, key: str):
        url = self.BASE_URL + "key"
        key = key.lstrip("/")
        params = {"v": key}
        response = self._client.delete(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Request failed with status {response.status_code}: {response.text}"
            )

    def get_secret_by_key(self, key):
        url = self.BASE_URL + "secret-value"
        params = {"v": key}
        response = self._client.get(url, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Request failed with status {response.status_code}: {response.text}"
            )

    def create_entry(self, key: str, value: str, secure=False):
        url = self.BASE_URL.rstrip("/")
        key = key.lstrip("/")
        data = [{
            "key": key,
            "value": value,
            "secure": secure
        }]

        response = self._client.post(url, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Request failed with status {response.status_code}: {response.text}"
            )

    def create_entries(self, entries_json):
        url = self.BASE_URL.rstrip("/")

        response = self._client.post(url, json=entries_json)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Request failed with status {response.status_code}: {response.text}"
            )