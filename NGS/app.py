def main():
    import streamlit as st 
    import requests
    from generate_date import date_today
    from generate_files import load_stations, generate_name_file

    df_estaciones = load_stations()

    # 2. Pedir coordenadas del usuario
    lat = float(input(" Ingrese su latitud (ej. 34.05): "))
    lon = float(input(" Ingrese su longitud (ej. -118.25): "))

    # 3. Pedir fecha
    fecha = input(" Ingrese la fecha (YYYY-MM-DD): ")
    anio, doy = date_today(fecha)

    # 4. Buscar estaciones cercanas y verificar archivos
    #df_cercanas = estaciones_mas_cercanas(df_estaciones, lat, lon)
    #df_cercanas = verificar_disponibilidad_rinex(df_cercanas, anio, doy, tipo='obs')

    # 5. Mostrar tabla
    print("\n🧭 Estaciones más cercanas:")
    #print(df_cercanas[['SITEID', 'Latitude', 'Longitude', 'Distancia_km', 'SAMPLING', 'AGENCY', 'STATUS', 'Disponible']].to_string(index=False))

    # 6. Selección válida de estación disponible
    while True:
        siteid = input("\n Ingrese el SITEID de una estación disponible (o escriba 'salir' para cancelar): ").strip().upper()

        if siteid.lower() == 'salir':
            print(" Operación cancelada por el usuario.")
            break

        fila_sel = df_cercanas[df_cercanas['SITEID'] == siteid]

        if fila_sel.empty:
            print(" El SITEID ingresado no está en la lista mostrada. Intente nuevamente.")
        elif fila_sel.iloc[0]['Disponible'] != "SI":
            print(f" El archivo de {siteid} para el {fecha} NO está disponible. Intente con otro.")
        else:
            url = fila_sel.iloc[0]['URL']
            descargar_archivo_rinex(url)
            print(f" ✔️ Archivo de {siteid} para el {fecha} descargado exitosamente.")
            break


if __name__ == "__main__":
    import sys
    sys.exit(main())