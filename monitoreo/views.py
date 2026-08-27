import json
from pathlib import Path
from django.conf import settings
from django.shortcuts import render
from django.http import Http404

DATA_DIR = Path(settings.BASE_DIR) / 'data'


def cargar_json(nombre_archivo):
    ruta = DATA_DIR / nombre_archivo
    if not ruta.exists():
        return []
    with open(ruta, 'r', encoding='utf-8') as f:
        return json.load(f)


def lista_zonas(request):
    zonas = cargar_json('zonas.json')
    dispositivos = cargar_json('dispositivos.json')

    # Calcular dinámicamente cantidad de dispositivos por zona
    for zona in zonas:
        zona['total_dispositivos'] = sum(
            1 for d in dispositivos if d.get('zona_id') == zona.get('id')
        )

    context = {
        'zonas': zonas
    }
    return render(request, 'monitoreo/lista_zonas.html', context)


def detalle_zona(request, zona_id):
    zonas = cargar_json('zonas.json')
    dispositivos = cargar_json('dispositivos.json')
    categorias = cargar_json('categorias.json')

    # Buscar la zona correspondiente
    zona = next((z for z in zonas if z.get('id') == zona_id), None)
    if zona is None:
        raise Http404("La zona solicitada no existe.")

    # Mapear categorías por ID para consulta rápida
    cat_map = {c.get('id'): c.get('nombre') for c in categorias}

    # Filtrar dispositivos de la zona y asociar nombre de categoría
    dispositivos_zona = []
    consumo_total = 0.0

    for d in dispositivos:
        if d.get('zona_id') == zona_id:
            consumo = float(d.get('consumo_kwh', 0.0))
            consumo_total += consumo
            dispositivos_zona.append({
                'id': d.get('id'),
                'nombre': d.get('nombre'),
                'categoria_nombre': cat_map.get(d.get('categoria_id'), 'Sin categoría'),
                'consumo_kwh': consumo
            })

    # Regla de estado: ALERTA si consumo_total > limite_kwh, sino NORMAL
    limite = float(zona.get('limite_kwh', 0.0))
    estado = 'ALERTA' if consumo_total > limite else 'NORMAL'

    context = {
        'zona': zona,
        'dispositivos': dispositivos_zona,
        'consumo_total': round(consumo_total, 2),
        'total_dispositivos': len(dispositivos_zona),
        'estado': estado,
    }
    return render(request, 'monitoreo/detalle_zona.html', context)