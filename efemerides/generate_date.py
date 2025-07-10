from datetime import datetime

def is_bisiesto(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
def calculate_doy(year, month, day):
    dias_por_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_bisiesto(year):
        dias_por_mes[1] = 29
    return sum(dias_por_mes[:month - 1]) + day
def obtener_anio_doy_semana(fecha_str):
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    anio = fecha.year
    doy = calculate_doy(anio, fecha.month, fecha.day)
    gps_epoch = datetime(1980, 1, 6)
    delta_dias = (fecha - gps_epoch).days
    semana_gps = delta_dias // 7
    return anio, doy, semana_gps
