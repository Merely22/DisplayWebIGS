import streamlit as st
from IGS.authenticator import SessionWithHeaderRedirection

def obtener_md5sums(semana_gps: int) -> list[str] | None:
    if "md5sums_cache" not in st.session_state:
        st.session_state["md5sums_cache"] = {}
    if semana_gps in st.session_state["md5sums_cache"]:
        return st.session_state["md5sums_cache"][semana_gps]
    url = f"https://cddis.nasa.gov/archive/gnss/products/{semana_gps}/MD5SUMS"
    try:
        session = SessionWithHeaderRedirection()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            archivos = [line.split()[-1] for line in response.text.strip().splitlines()]
            st.session_state["md5sums_cache"][semana_gps] = archivos
            return archivos
        elif response.status_code == 401:
            st.warning("⚠️Not Access.")
        elif response.status_code == 404:
            st.warning(f"⚠️ Not Found MD5SUMS in the GPS week {semana_gps}")
        else:
            st.warning(f"⚠️ Error {response.status_code}: {response.reason}")
    except Exception as e:
        st.error(f"❌ Error MD5SUMS: {e}")
    return None
def archivo_esta_disponible(nombre_archivo: str, semana_gps: int) -> bool:
    archivos = obtener_md5sums(semana_gps)
    return nombre_archivo in archivos if archivos else False