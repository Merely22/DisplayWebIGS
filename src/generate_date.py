def es_bisiesto(anio):
    return (anio % 4 == 0 and anio % 100 != 0) or (anio % 400 == 0)

def calculate_date(anio, mes, dia):
    dias_por_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if es_bisiesto(anio):
        dias_por_mes[1] = 29
    day_year = sum(dias_por_mes[:mes - 1]) + dia
    return str(day_year).zfill(3)
