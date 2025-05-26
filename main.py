# main.py (para integrar todos los módulos)
from src.autenticador import AutenticadorEarthData
from src.generate_date import calcular_dia_anio, obtener_fecha_formateada
from src.generate_files import GeneradorArchivos
from src.maps import VisualizadorEstaciones

def main():
    # Paso 1: Seleccionar estación
    visualizador = VisualizadorEstaciones()
    visualizador.mostrar_estaciones()
    estacion = visualizador.seleccionar_estacion()

    # Paso 2: Ingresar fecha
    print(f"\nSeleccione la fecha para obtención de sus datos de la estación {estacion}:")
    anio = int(input("Ingrese el año: "))
    mes = int(input("Ingrese el mes: "))
    dia = int(input("Ingrese el dia: "))

    # Calcular fechas
    dia_del_anio = calcular_dia_anio(anio, mes, dia)
    fecha_texto = obtener_fecha_formateada(anio, mes, dia)

    # Paso 3: Autenticación y descarga
    autenticador = AutenticadorEarthData()
    generador = GeneradorArchivos(autenticador.obtener_sesion())
    
    carpeta_salida = generador.crear_carpeta_salida(estacion, fecha_texto)
    vinculos = generador.obtener_vinculos(anio, dia_del_anio, estacion)
    generador.descargar_archivos(vinculos, carpeta_salida)

    # Paso 4: Comprimir resultados
    visualizador.comprimir_datos(estacion, fecha_texto)

if __name__ == "__main__":
    main()