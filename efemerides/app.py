import streamlit as st
from efemerides.generate_date import obtener_anio_doy_semana
from efemerides.generate_files import construir_url_sp3, descargar_y_descomprimir_sp3
from efemerides.instituciones_diccionario import instituciones
from efemerides.summary_checker import archivo_esta_disponible

def main():
    st.title("📡 Precise Orbits Download")

    # Selección de institución
    institucion = st.selectbox("Select the ephemeris-generating institution:", list(instituciones.keys()))
    st.subheader(instituciones[institucion]["nombre"])
    st.image(instituciones[institucion]["logo"], width=200)
    st.markdown(instituciones[institucion]["descripcion"])

    # Tipo de efeméride
    tipo_efemeride = st.radio("Type of Orbits", ["Final Solution", "Rapid Solution"], horizontal=True)

    # Selección de fecha
    fecha = st.date_input("Select date", format="YYYY-MM-DD")

    if st.button("🔍 Search for available orbits"):
        # Procesar fecha
        fecha_str = fecha.strftime("%Y-%m-%d")
        anio, doy, semana = obtener_anio_doy_semana(fecha_str)
        producto_deseado = "FIN" if tipo_efemeride == "Final Solution" else "RAP"

        # Limpiar session_state previo
        for clave in list(st.session_state.keys()):
            if clave.startswith("url_") or clave.startswith("nombre_"):
                del st.session_state[clave]

        # Buscar productos compatibles
        productos_validos = [
            p for p in instituciones[institucion]["productos"]
            if p["producto"] == producto_deseado
        ]
        if not productos_validos:
            st.warning(f"The institution {institucion} does not have products {producto_deseado}.")
            return
        for producto in productos_validos:
            tipo = producto["tipo"]
            muestreo = producto["sampling"]
            url, nombre_archivo = construir_url_sp3(semana, institucion, tipo, producto_deseado, anio, doy, muestreo)

            if archivo_esta_disponible(nombre_archivo, semana):
                key_url = f"url_{tipo}"
                key_nombre = f"nombre_{tipo}"
                st.session_state[key_url] = url
                st.session_state[key_nombre] = nombre_archivo
                st.success(f"✅ File available: {nombre_archivo}")
                
            else:
                st.warning(f"⚠️ The file {nombre_archivo} is not yet available on the server.")

    # Botón único para descargar todo
    tipos_disponibles = [k.replace("url_", "") for k in st.session_state if k.startswith("url_")]
    if tipos_disponibles:
        if st.button("⬇️ Download all (.SP3)"):
            for tipo in tipos_disponibles:
                url = st.session_state[f"url_{tipo}"]
                nombre = st.session_state[f"nombre_{tipo}"]
                ruta = descargar_y_descomprimir_sp3(url, nombre)

                if ruta:
                    st.success(f"📥 {tipo} uncompressed: {ruta.name}")
                    st.download_button(f"📎 Download File", ruta.read_bytes(), file_name=ruta.name)
                else:
                    st.error(f"❌The file could not be downloaded {nombre}")

if __name__ == "__main__":
    main()
