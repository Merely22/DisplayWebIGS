from datetime import datetime

def is_bisiesto(year):
    """Verifica si un año es bisiesto."""
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def calculate_date(year, month, day):
    """
    Convierte una fecha (año, mes, día) a número de día del año (DOY).
    Considera años bisiestos.
    """
    dias_por_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_bisiesto(year):
        dias_por_mes[1] = 29
    return sum(dias_por_mes[:month - 1]) + day

def fecha_a_doy(fecha_str):
    """
    Convierte una fecha en formato 'YYYY-MM-DD' a (año, DOY).
    """
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    anio = fecha.year
    doy = calculate_date(fecha.year, fecha.month, fecha.day)
    return anio, doy

def is_within_range(input_date):
    today = datetime.today().date()  # Convertir a date
    delta = today - input_date       # input_date ya debe ser tipo date
    return delta.days <= 182, delta.days
