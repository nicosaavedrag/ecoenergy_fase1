# Análisis de Datos y Arquitectura - EcoEnergy Fase 1

## 1. Modelo Relacional y Multiplicidades
- **Zona (1) -> (0..*) Dispositivo**: Una zona puede contener cero o múltiples dispositivos. Cada dispositivo pertenece obligatoriamente a una zona mediante la clave `zona_id`.
- **Categoria (1) -> (0..*) Dispositivo**: Una categoría clasifica cero o múltiples dispositivos. Cada dispositivo posee una categoría asignada mediante la clave `categoria_id`.

## 2. Claves de Conexión
- `dispositivos.json.zona_id` -> `zonas.json.id`
- `dispositivos.json.categoria_id` -> `categorias.json.id`

## 3. Matriz de Criterios de Aceptación y Pruebas
| Criterio de Aceptación | Archivo / Componente | Prueba Realizada |
| :--- | :--- | :--- |
| **CA-01 a CA-05**: Listados y detalles dinámicos | `views.py` / `templates` | Cálculo dinámico de métricas y estados NORMAL/ALERTA superado. |
| **CA-06 y CA-07**: Casos de borde y nuevos datos | `views.py` / `json` | Zonas sin dispositivos manejadas correctamente. |
| **CA-08**: Identificador inexistente controlado | `views.py` (`Http404`) | Consulta a zonas inexistentes arroja error 404 controlado. |
| **CA-09 a CA-12**: UX/UI y Accesibilidad | `base.html` / `bootstrap5` | Jerarquía visual clara, tablas responsivas y uso de badges. |
| **CA-13**: Verificación técnica | `manage.py check` | Ejecución superada con 0 problemas detectados. |
