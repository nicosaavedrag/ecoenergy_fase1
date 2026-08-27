# EcoEnergy - Sistema de Monitoreo Energético (Fase 1)

Aplicación web desarrollada en Django para el monitoreo y control de consumo energético por zonas y dispositivos, utilizando estructuras JSON como fuente de datos desacoplada.

## Requisitos
- Python 3.10+
- Django 4.2+
- django-bootstrap-v5

## Instalación y Ejecución
1. Activar el entorno virtual: .venv\Scripts\activate
2. Instalar las dependencias: pip install -r requirements.txt
3. Iniciar el servidor local: python manage.py runserver
4. Acceder en el navegador a: [http://127.0.0.1:8000/zonas/](http://127.0.0.1:8000/zonas/)

## Rutas Disponibles
- /zonas/: Listado general de zonas de consumo con límites y conteo.
- /zonas/<id>/: Vista de detalle con estado (NORMAL/ALERTA).
