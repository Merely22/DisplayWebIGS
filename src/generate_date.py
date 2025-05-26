# Módulo 2: Generador de Fechas
class GeneradorFechas:
    @staticmethod
    def es_bisiesto(anio):
        return (anio % 4 == 0 and anio % 100 != 0) or (anio % 400 == 0)

    @staticmethod
    def calcular_dia_anio(anio, mes, dia):
        dias_por_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if GeneradorFechas.es_bisiesto(anio):
            dias_por_mes[1] = 29
        diadelanio = sum(dias_por_mes[:mes - 1]) + dia
        return str(diadelanio).zfill(3)

    @staticmethod
    def obtener_fecha_formateada(anio, mes, dia):
        return f"{anio}-{str(mes).zfill(2)}-{str(dia).zfill(2)}"