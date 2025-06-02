import requests
from dotenv import load_dotenv
import os

load_dotenv()  # Carga desde .env
_USERNAME = os.getenv("NASA_USERNAME")
_PASSWORD = os.getenv("NASA_PASSWORD")

class SessionWithHeaderRedirection(requests.Session):
    AUTH_HOST = 'urs.earthdata.nasa.gov'

    def __init__(self):
        super().__init__()
        self.auth = (_USERNAME, _PASSWORD)

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        original_parsed = requests.utils.urlparse(response.request.url)
        redirect_parsed = requests.utils.urlparse(prepared_request.url)
        if (original_parsed.hostname != redirect_parsed.hostname) and \
           (redirect_parsed.hostname != self.AUTH_HOST) and \
           (original_parsed.hostname != self.AUTH_HOST):
            del headers['Authorization']
