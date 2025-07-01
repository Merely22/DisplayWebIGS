from datetime import datetime

def is_bisiesto(year):
    """Verifica si un año es bisiesto."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def calculate_doy(year, month, day):
    """Convierte una fecha a número de día del año (DOY)."""
    dias_por_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_bisiesto(year):
        dias_por_mes[1] = 29
    return sum(dias_por_mes[:month - 1]) + day

def fecha_a_gpsweek_doy(fecha_str):
    """
    Convierte una fecha en formato 'YYYY-MM-DD' a (semana GPS, DOY).
    """
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    anio = fecha.year
    doy = calculate_doy(anio, fecha.month, fecha.day)
    
    # Fecha de inicio del tiempo GPS: 1980-01-06
    gps_start = datetime(1980, 1, 6)
    delta = fecha - gps_start
    gps_week = delta.days // 7

    return gps_week, doy