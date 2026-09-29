# EcoEnergy - Plataforma de Monitoreo y Gestión Energética

Sistema web desarrollado con **Django** para la supervisión y control del consumo energético industrial, multiorganización y multi-zona. Incluye interfaces para consulta operativa y un **Django Admin** profesional con scoping estricto por organización, validaciones de negocio controladas, inlines y acciones en lote.

---

## 🚀 Requisitos del Sistema
- **Python:** 3.10 o superior (probado en Python 3.12)
- **Django:** 4.2 LTS
- **Entorno virtual:** `venv`

---

## 🛠️ Instalación y Puesta en Marcha (Entorno Limpio)

Siga estos pasos para levantar el proyecto desde cero en el laboratorio o en cualquier equipo:

### 1. Clonar o acceder al directorio del proyecto
```bash
cd ecoenergy_fase1
```

### 2. Crear y activar el entorno virtual
En Windows (PowerShell / CMD):
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```
*(En Linux / macOS: `python3 -m venv .venv && source .venv/bin/activate`)*

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno (`.env`)
Copie el archivo de ejemplo `.env.example` creando su archivo `.env`:
```powershell
Copy-Item .env.example .env
```
*(O en CMD: `copy .env.example .env`)*

El archivo `.env` ya viene preconfigurado para SQLite por defecto (máxima portabilidad).

### 5. Aplicar migraciones
```bash
python manage.py migrate
```

### 6. Cargar datos de prueba reproducibles (Seed Command)
Ejecute el comando de poblamiento para crear automáticamente las organizaciones, tablas maestras, transacciones operativas, grupos, permisos y usuarios de prueba:
```bash
python manage.py poblar_datos --limpiar
```

### 7. Iniciar el servidor de desarrollo
```bash
python manage.py runserver
```
Abra en el navegador: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 👥 Cuentas de Prueba Documentadas

El comando `poblar_datos` crea 3 usuarios con diferentes niveles de acceso y organizaciones asociadas:

| Usuario | Contraseña | Rol / Contexto | Permisos en Django Admin |
| :--- | :--- | :--- | :--- |
| **`admin`** | `AdminPassword123!` | **Superusuario Global** | Acceso total sin restricciones a todas las organizaciones y tablas. |
| **`operador_norte`** | `OperadorNorte123!` | **Operador EcoIndustrias Norte S.A.** | Solo visualiza y gestiona zonas, dispositivos, mediciones y alertas de **EcoIndustrias Norte S.A.**. No puede ver datos de EcoRetail Sur. |
| **`operador_sur`** | `OperadorSur123!` | **Operador EcoRetail Sur SpA** | Solo visualiza y gestiona zonas, dispositivos, mediciones y alertas de **EcoRetail Sur SpA**. No puede ver datos de EcoIndustrias Norte. |

---

## 🧪 Pruebas de Demostración en Laboratorio (Evaluación Sumativa II)

### 1. Demostración de Scoping y Seguridad por Organización
1. Iniciar sesión como `operador_norte`:
   - Ir a **Zonas** o **Dispositivos**: solo se listan los equipos pertenecientes a *EcoIndustrias Norte S.A.*.
   - En el formulario de creación de Dispositivos, el selector de Zona únicamente muestra zonas de su propia empresa.
2. Cerrar sesión e iniciar sesión como `operador_sur`:
   - Ir a **Zonas** o **Dispositivos**: únicamente se visualizan los registros de *EcoRetail Sur SpA*.
3. Iniciar sesión como `admin`:
   - Se visualizan todos los registros y todas las organizaciones.

### 2. Demostración de Admin Pro (Inlines, Acciones y Validaciones)
- **Inline de Dispositivos:** Al editar cualquier **Zona**, en la parte inferior aparece la tabla inline editable con todos los dispositivos de dicha zona.
- **Acciones Personalizadas en Lote:**
  - En **Dispositivos**: seleccionar elementos y elegir en la barra superior *"Marcar dispositivos seleccionados: EN MANTENIMIENTO"* o *"Marcar dispositivos seleccionados: ACTIVO"*.
  - En **Alertas de Consumo**: seleccionar alertas y ejecutar *"Marcar alertas seleccionadas como RESUELTAS"*.
- **Validación Controlada con `clean()`:**
  - Intentar editar una **Zona** con un `limite_kwh <= 0` (por ejemplo, `-50`): el sistema muestra un mensaje de error amigable en rojo sin romper la aplicación.
  - Intentar crear un **Dispositivo** con estado `ACTIVO` y `potencia_nominal_kw = 0`: se rechaza indicando que un dispositivo activo requiere potencia > 0 kW.
  - Intentar guardar un **Registro de Consumo** con consumo negativo o fecha futura: se valida controladamente.

### 3. Ejecución de Tests Automatizados
Para comprobar toda la suite de pruebas unitarias y de integración:
```bash
python manage.py test monitoreo
```

---

## 🌐 Rutas del Sistema
- **Django Admin:** `/admin/`
- **Listado de Zonas (Fase 1):** `/zonas/`
- **Detalle de Zona (Fase 1):** `/zonas/<id>/`
- **Resumen Comparativo (Fase 2):** `/resumen-zonas/`
