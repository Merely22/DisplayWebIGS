import requests
from dotenv import load_dotenv
import os

def get_credentials():
    load_dotenv()  # Funciona en local; en producción no afecta si .env no existe
    username = os.getenv("NASA_USERNAME")
    password = os.getenv("NASA_PASSWORD")
    return username, password

class SessionWithHeaderRedirection(requests.Session):
    AUTH_HOST = 'urs.earthdata.nasa.gov'

    def __init__(self):
        super().__init__()
        username, password = get_credentials()
        self.auth = (username, password)

    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        original_parsed = requests.utils.urlparse(response.request.url)
        redirect_parsed = requests.utils.urlparse(prepared_request.url)
        if (original_parsed.hostname != redirect_parsed.hostname) and \
           (redirect_parsed.hostname != self.AUTH_HOST) and \
           (original_parsed.hostname != self.AUTH_HOST):
            headers.pop('Authorization', None)
