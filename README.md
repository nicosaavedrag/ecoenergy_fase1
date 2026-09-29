# EcoEnergy - Plataforma de Monitoreo y Gestión Energética Industrial
### Evaluación Formativa · Unidad II (Integración Django: Autenticación, Permisos, CRUD, Archivos y Despliegue)
**Asignatura:** Programación Back End (TI3V41)  
**Sede:** INACAP La Serena · **Docente:** Javier Ahumada  

---

## 📌 Descripción General
**EcoEnergy** es una solución integral desarrollada en Django orientada a la supervisión, auditoría y control de consumo eléctrico para empresas industriales y comerciales multi-sede.

El sistema incorpora:
- **Estructura modular en 2 aplicaciones:** `accounts` (autenticación, roles y recuperación de clave) y `monitoreo` (lógica de negocio y telemetría).
- **Modelo de datos con nomenclatura técnica en inglés:** 6 tablas maestras y 4 operacionales con borrado lógico (`deleted_at`).
- **Autenticación robusta:** Inicio/cierre de sesión, recuperación de contraseña mediante **código numérico de 6 dígitos** (de un solo uso y expiración temporal) y validador de complejidad (mínimo 10 caracteres, mayúscula, minúscula, número y símbolo).
- **4 CRUDs completos en interfaz web:** Zonas, Dispositivos, Mediciones de Consumo y Alertas.
- **Manejo de archivos e imágenes:** Subida de fotografías/fichas técnicas de equipos con validación de extensión, límite de tamaño (máx. 2 MB) y contenido real verificado con **Pillow** (`Image.verify()`).
- **Paginación dinámica en sesión:** Selector de 5, 15 y 30 registros por página persistido en `request.session`.
- **Eliminación segura con SweetAlert2:** Diálogos modales interactivos con envío por `POST + CSRF` que ejecutan borrado lógico.
- **Exportación a Excel (`.xlsx`):** Descarga de reportes reales generados dinámicamente con `openpyxl`.
- **Carga masiva reproducible:** Generación de **más de 1.100 registros de negocio** mediante comando de gestión.
- **Despliegue preparado para AWS Academy:** Scripts automatizados y guía detallada para EC2.

---

## 🛠️ Requisitos Previos
- Python 3.10 o superior (verificado en Python 3.12).
- Git.
- Entorno virtual `venv`.

---

## 🚀 Instalación y Puesta en Marcha Local

### 1. Clonar el repositorio y acceder a la carpeta
```bash
git clone <URL_REPOSITORIO>
cd ecoenergy_fase1
```

### 2. Crear y activar el entorno virtual
En Windows:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```
En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno (`.env`)
```powershell
Copy-Item .env.example .env
```
*(En Linux/macOS: `cp .env.example .env`)*

### 5. Aplicar migraciones
```bash
python manage.py migrate
```

### 6. Cargar datos reproducibles (>= 1.000 registros)
```bash
python manage.py poblar_datos --limpiar
```

### 7. Ejecutar suite de pruebas automatizadas
```bash
python manage.py test monitoreo
```

### 8. Iniciar el servidor local
```bash
python manage.py runserver
```
Abra en su navegador: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 👥 Cuentas de Prueba Documentadas

| Usuario | Contraseña | Rol en el Sistema | Alcance / Scoping de Datos |
| :--- | :--- | :--- | :--- |
| **`admin`** | `AdminPassword123!` | Superadministrador Global | Acceso total a todas las empresas, zonas y configuraciones. |
| **`operador_norte`** | `OperadorNorte123!` | Operador / Editor | Solo gestiona datos de **EcoIndustrias Norte S.A.** (Crear, editar, eliminar lógicamente). |
| **`lector_norte`** | `LectorNorte123!` | Lector / Consulta | Solo visualiza y exporta datos de **EcoIndustrias Norte S.A.** (Sin permisos de modificación). |
| **`operador_sur`** | `OperadorSur123!` | Operador / Editor | Solo gestiona datos de **EcoRetail Sur SpA**. Aislado de la empresa Norte. |

---

## 🌐 Módulos y Rutas Principales

### Autenticación y Cuentas
- Iniciar Sesión: `/accounts/login/`
- Cerrar Sesión: `/accounts/logout/`
- Recuperar Contraseña (Código 6 dígitos): `/accounts/password-reset/`
- Validar Código y Nueva Clave: `/accounts/password-reset/verify/`
- Perfil de Usuario: `/accounts/profile/`

### Gestión Operativa y CRUDs
- Dashboard Ejecutivo: `/dashboard/`
- CRUD Zonas: `/zones/`
- CRUD Dispositivos (con fotos): `/devices/`
- CRUD Mediciones de Consumo: `/consumption/`
- Descarga Reporte Excel: `/consumption/?export=xlsx`
- CRUD Alertas e Incidencias: `/alerts/`
- Administrador Django: `/admin/`

---

## ☁️ Despliegue en AWS Academy
Consulte el archivo [AWS_ACADEMY_DEPLOYMENT.md](file:///c:/Users/nicol/Documents/ecoenergy_fase1/AWS_ACADEMY_DEPLOYMENT.md) y ejecute `./deploy_aws.sh` en su instancia EC2 de AWS Academy para desplegar en menos de 2 minutos.
