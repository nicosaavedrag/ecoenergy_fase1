import json
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.shortcuts import render

DATA_DIR = Path(settings.BASE_DIR) / 'data'


def cargar_json(nombre_archivo):
    ruta = DATA_DIR / nombre_archivo
    if not ruta.exists():
        return []
    with open(ruta, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def lista_zonas(request):
    zonas = cargar_json('zonas.json')
    dispositivos = cargar_json('dispositivos.json')

    for zona in zonas:
        zona['total_dispositivos'] = sum(
            1 for d in dispositivos if d.get('zona_id') == zona.get('id')
        )

    context = {'zonas': zonas}
    return render(request, 'monitoreo/lista_zonas.html', context)


def detalle_zona(request, zona_id):
    zonas = cargar_json('zonas.json')
    dispositivos = cargar_json('dispositivos.json')
    categorias = cargar_json('categorias.json')

    zona = next((z for z in zonas if z.get('id') == zona_id), None)
    if zona is None:
        raise Http404("La zona solicitada no existe.")

    cat_map = {c.get('id'): c.get('nombre') for c in categorias}
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
                'consumo_kwh': consumo,
            })

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


def resumen_zonas(request):
    zonas = cargar_json('zonas.json')
    dispositivos = cargar_json('dispositivos.json')

    total_zonas = len(zonas)
    total_dispositivos = len(dispositivos)
    consumo_global = sum(float(d.get('consumo_kwh', 0.0)) for d in dispositivos)

    lista_resumen = []
    for zona in zonas:
        disp_zona = [d for d in dispositivos if d.get('zona_id') == zona.get('id')]
        cantidad = len(disp_zona)
        consumo_total = sum(float(d.get('consumo_kwh', 0.0)) for d in disp_zona)
        limite = float(zona.get('limite_kwh', 0.0))

        if consumo_total <= limite:
            estado_texto = 'DENTRO DEL LÍMITE'
            estado_clase = 'bg-success text-white'
        else:
            estado_texto = 'LÍMITE SUPERADO'
            estado_clase = 'bg-danger text-white'

        lista_resumen.append({
            'nombre': zona.get('nombre', 'Sin nombre'),
            'cantidad': cantidad,
            'consumo_total': consumo_total,
            'limite': limite,
            'estado_texto': estado_texto,
            'estado_clase': estado_clase,
        })

    context = {
        'total_zonas': total_zonas,
        'total_dispositivos': total_dispositivos,
        'consumo_global': consumo_global,
        'zonas': lista_resumen,
    }
    return render(request, 'monitoreo/resumen_zonas.html', context)
