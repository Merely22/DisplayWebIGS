from datetime import datetime

def fecha_a_doy(fecha_str):
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    anio = fecha.year
    doy = fecha.timetuple().tm_yday
    return anio, doy
