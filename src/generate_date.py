from datetime import datetime

def is_bisiesto(year):
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def calculate_date(year, month, day):
    dias_por_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if is_bisiesto(year):
        dias_por_mes[1] = 29
    return sum(dias_por_mes[:month - 1]) + day

def is_within_range(input_date):
    today = datetime.today()
    delta = today - input_date
    return delta.days <= 182, delta.days
