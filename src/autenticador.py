import streamlit as st
import requests

# Módulo 1: Autenticador
class AutenticadorEarthData:
    def __init__(self):
        self.usuario = st.secrets["earthdata"]["username"]
        self.contrasena = st.secrets["earthdata"]["password"]
        self.session = self._crear_sesion()

    class SessionWithHeaderRedirection(requests.Session):
        AUTH_HOST = 'urs.earthdata.nasa.gov'

        def __init__(self, username, password):
            super().__init__()
            self.auth = (username, password)

        def rebuild_auth(self, prepared_request, response):
            headers = prepared_request.headers
            original_parsed = requests.utils.urlparse(response.request.url)
            redirect_parsed = requests.utils.urlparse(prepared_request.url)
            if (original_parsed.hostname != redirect_parsed.hostname) and \
               (redirect_parsed.hostname != self.AUTH_HOST) and \
               (original_parsed.hostname != self.AUTH_HOST):
                del headers['Authorization']

    def _crear_sesion(self):
        session = self.SessionWithHeaderRedirection(self.usuario, self.contrasena)
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        return session
