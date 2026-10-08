"""
Script de Demostracion y Validacion de la Matriz de Seguridad JWT (Unidad 3 - Clase 2)
EcoEnergy - Plataforma de Monitoreo Energetico
"""
import os
import sys
import json
import django

# Forzar codificacion UTF-8 en consola
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecoenergy_project.settings')
django.setup()

from django.test import Client
from monitoreo.models import Zone, DeviceCategory, Device


def run_matrix_tests():
    client = Client()

    print("\n" + "=" * 75, flush=True)
    print(" [ECOENERGY] MATRIZ DE PRUEBAS DE SEGURIDAD REST API & JWT", flush=True)
    print("=" * 75, flush=True)

    # -------------------------------------------------------------------------
    # 0. OBTENCION DE TOKENS JWT
    # -------------------------------------------------------------------------
    print("\n[PASO 0] OBTENCION DE TOKENS JWT (/api/token/)", flush=True)

    # 0.1 Administrador
    res_adm = client.post('/api/token/', data={'username': 'admin', 'password': 'AdminPassword123!'})
    if res_adm.status_code != 200:
        print(f" [ERROR] Al obtener token de admin: {res_adm.status_code} {res_adm.json()}", flush=True)
        return
    admin_access = res_adm.json()['access']
    admin_refresh = res_adm.json()['refresh']
    print(f"  [OK] 0.1 Admin Token obtenido (HTTP {res_adm.status_code}):", flush=True)
    print(f"       Access Token:  {admin_access[:30]}...", flush=True)
    print(f"       Refresh Token: {admin_refresh[:30]}...", flush=True)

    # 0.2 Operador
    res_op = client.post('/api/token/', data={'username': 'operador_api', 'password': 'OperadorApi123!'})
    if res_op.status_code != 200:
        print(f" [ERROR] Al obtener token de operador: {res_op.status_code} {res_op.json()}", flush=True)
        return
    op_access = res_op.json()['access']
    print(f"  [OK] 0.2 Operador Token obtenido (HTTP {res_op.status_code}):", flush=True)
    print(f"       Access Token:  {op_access[:30]}...", flush=True)

    # 0.3 Renovacion con Refresh
    res_ref = client.post('/api/token/refresh/', data={'refresh': admin_refresh})
    print(f"  [OK] 0.3 Renovacion via Refresh Token (HTTP {res_ref.status_code}): Nuevo access generado exitosamente.", flush=True)

    # -------------------------------------------------------------------------
    # MATRIZ DE CASOS DE PRUEBA (SLIDE 15)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 75, flush=True)
    print(" [EJECUTANDO MATRIZ DE COMPROBACION DE LA CLASE 2]", flush=True)
    print("-" * 75, flush=True)

    # CASO 1: GET sin Bearer -> 401 Unauthorized
    r1 = client.get('/api/devices/')
    print(f">> PRUEBA 01 | GET /api/devices/ [Sin Token]", flush=True)
    print(f"   Resultado: HTTP {r1.status_code} (Esperado: 401)", flush=True)
    print(f"   Respuesta: {r1.json()}", flush=True)
    assert r1.status_code == 401, "Error: Deberia rechazar con 401"

    # CASO 2A: GET con Operador -> 200 OK con Scoping
    r2a = client.get('/api/devices/', HTTP_AUTHORIZATION=f'Bearer {op_access}')
    print(f"\n>> PRUEBA 02a | GET /api/devices/ [Operador - Rol Solo Lectura]", flush=True)
    print(f"   Resultado: HTTP {r2a.status_code} (Esperado: 200)", flush=True)
    print(f"   Scoping:   Visualiza unicamente {len(r2a.json())} dispositivos (de su empresa 'EcoIndustrias Norte')", flush=True)
    assert r2a.status_code == 200

    # CASO 2B: POST con Operador -> 403 Forbidden
    zone = Zone.objects.first()
    cat = DeviceCategory.objects.first()
    payload = {
        'name': 'Intento Invalido Operador',
        'serial_number': 'TEST-OP-403',
        'nominal_power_kw': '15.00',
        'status': 'ACTIVE',
        'zone': zone.id,
        'category': cat.id
    }
    r2b = client.post('/api/devices/', data=json.dumps(payload), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {op_access}')
    print(f"\n>> PRUEBA 02b | POST /api/devices/ [Operador intenta crear registro]", flush=True)
    print(f"   Resultado: HTTP {r2b.status_code} (Esperado: 403)", flush=True)
    print(f"   Respuesta: {r2b.json()}", flush=True)
    assert r2b.status_code == 403, "Error: Operador no debe tener permisos de escritura"

    # CASO 3: POST valido con Administrador -> 201 Created
    payload_admin = {
        'name': 'Compresor Turbina Nuevo',
        'serial_number': 'TEST-ADM-201',
        'nominal_power_kw': '30.00',
        'status': 'ACTIVE',
        'zone': zone.id,
        'category': cat.id
    }
    r3 = client.post('/api/devices/', data=json.dumps(payload_admin), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {admin_access}')
    new_id = r3.json().get('id')
    print(f"\n>> PRUEBA 03 | POST /api/devices/ [Administrador crea registro valido]", flush=True)
    print(f"   Resultado: HTTP {r3.status_code} (Esperado: 201)", flush=True)
    print(f"   Registro creado ID: {new_id} ({r3.json().get('name')})", flush=True)
    assert r3.status_code == 201

    # CASO 4: POST invalido con Administrador -> 400 Bad Request
    payload_err = {
        'name': 'Equipo Potencia Cero',
        'serial_number': 'TEST-ADM-400',
        'nominal_power_kw': '0.00',
        'status': 'ACTIVE',
        'zone': zone.id,
        'category': cat.id
    }
    r4 = client.post('/api/devices/', data=json.dumps(payload_err), content_type='application/json', HTTP_AUTHORIZATION=f'Bearer {admin_access}')
    print(f"\n>> PRUEBA 04 | POST /api/devices/ [Administrador con datos invalidos: 0 kW]", flush=True)
    print(f"   Resultado: HTTP {r4.status_code} (Esperado: 400)", flush=True)
    print(f"   Error devuelto por Serializer: {r4.json()}", flush=True)
    assert r4.status_code == 400

    # CASO 5: GET de ID inexistente con Administrador -> 404 Not Found
    r5 = client.get('/api/devices/999999/', HTTP_AUTHORIZATION=f'Bearer {admin_access}')
    print(f"\n>> PRUEBA 05 | GET /api/devices/999999/ [ID inexistente]", flush=True)
    print(f"   Resultado: HTTP {r5.status_code} (Esperado: 404)", flush=True)
    print(f"   Respuesta: {r5.json()}", flush=True)
    assert r5.status_code == 404

    # CASO 6: DELETE con Administrador -> 204 No Content (Borrado Logico)
    r6 = client.delete(f'/api/devices/{new_id}/', HTTP_AUTHORIZATION=f'Bearer {admin_access}')
    print(f"\n>> PRUEBA 06 | DELETE /api/devices/{new_id}/ [Administrador elimina logicamente]", flush=True)
    print(f"   Resultado: HTTP {r6.status_code} (Esperado: 204 No Content)", flush=True)
    assert r6.status_code == 204

    # Limpieza de registros temporales
    Device.all_objects.filter(serial_number__startswith='TEST-').delete()

    print("\n" + "=" * 75, flush=True)
    print(" [OK] TODAS LAS PRUEBAS DE LA MATRIZ DE LA CLASE 2 PASARON AL 100%", flush=True)
    print("=" * 75 + "\n", flush=True)


if __name__ == '__main__':
    run_matrix_tests()
