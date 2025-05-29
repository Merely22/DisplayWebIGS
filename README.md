# **README - Web Scraping & Visualización de Datos IGS**  

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)  
![Streamlit](https://img.shields.io/badge/Streamlit-1.45+-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)  
![Requests](https://img.shields.io/badge/Requests-HTTP%20Client-important?style=for-the-badge)  

## **🌐 Descripción**  
Aplicación de **web scraping** que utiliza la librería `requests` para extraer datos de estaciones GNSS del servicio IGS (International GNSS Service) 
(https://network.igs.org/).  

**Características principales**:  
- 🕸️ Extracción de datos mediante `requests` 
- 📍 Cálculo de distancias geodésicas con `geopy`  
- 🗺️ Visualización interactiva con `streamlit-folium`  
- ⏱️ Programación de actualizaciones automáticas  

## **📂 Estructura del Proyecto**  
```
WebDisplay/
├── src/
│   ├── authenticator.py    # Manejo de credenciales
│   ├── generate_date.py    # Utilidades de fecha
│   ├── generate_files.py   # Generación de archivos
│   ├── maps.py             # Visualización de mapas
│   ├── nearest_station.py  # Cálculo de estaciones cercanas
├── app.py                  # Aplicación principal
├── igs_stations.csv        # Dataset de estaciones
├── requirements.txt        # Dependencias
└── .gitignore 
└── README.md
```

**Flujo de trabajo**:  
1. Autenticación con ANS vía `requests`  
2. Descarga y parseo de datos IGS  
3. Procesamiento geoespacial  
4. Generación de visualizaciones  

## **⚠️ Consideraciones Legales**  
- Este proyecto utiliza datos públicos de ANS ([ans.gov](https://www.ans.gov))  
- Cumple con los términos de servicio del proveedor  
- Se recomienda implementar delays entre requests  

## **📌 Requisitos**  
```txt
requests==2.32.3
streamlit==1.45.1
geopy==2.4.1
python-dotenv==1.0.0
```

## **📄 Licencia**  
MIT License © 2024 [Tu Nombre]  

> **Nota**: Este proyecto es para fines educativos. Verificar políticas de scraping de ANS antes de implementar en producción.
> Proyecto desarrollado bajo la coordinacion del Area de I+D - Mettatec 

## **📬 Contacto**  
✉️ **merely@mettatec.com**  
---
¡Gracias por tu interés en el proyecto! 🚀
