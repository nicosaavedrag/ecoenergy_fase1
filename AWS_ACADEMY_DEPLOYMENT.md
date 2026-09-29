# Guía de Despliegue en AWS Academy
## Proyecto EcoEnergy · Evaluación Formativa Unidad II

Esta guía detalla los pasos para desplegar la aplicación Django en una instancia **EC2** dentro del entorno **AWS Academy Learner Lab**.

---

### Paso 1: Iniciar el Laboratorio en AWS Academy
1. Inicie sesión en **AWS Academy** e ingrese al curso correspondiente.
2. Vaya a **Learner Lab** y presione el botón **Start Lab**.
3. Espere hasta que el indicador de estado cambie a **verde** (`AWS: online`).
4. Haga clic en **AWS** (con el círculo verde) para abrir la consola de administración de AWS en una nueva pestaña.

---

### Paso 2: Lanzar una Instancia EC2
1. En la consola de AWS, busque y seleccione el servicio **EC2**.
2. Haga clic en **Launch Instance** (Lanzar instancia):
   - **Name:** `EcoEnergy-Server`
   - **AMI:** `Ubuntu Server 24.04 LTS` o `Ubuntu Server 22.04 LTS` (64-bit x86).
   - **Instance type:** `t2.micro` (Apta para la capa gratuita / Learner Lab).
   - **Key pair (login):** Seleccione `vockey` (la llave por defecto de AWS Academy) o cree una nueva según su preferencia.
   - **Network settings (Security Group):**
     - Seleccione **Create security group**.
     - Marque **Allow SSH traffic** (Puerto 22).
     - Marque **Allow HTTP traffic** (Puerto 80).
     - Agregue una regla personalizada (**Custom TCP Rule**):
       - **Port range:** `8000`
       - **Source:** `Anywhere-IPv4` (`0.0.0.0/0`)
3. Haga clic en **Launch Instance**.

---

### Paso 3: Conectarse a la Instancia por SSH / EC2 Instance Connect
1. En la lista de instancias EC2, seleccione `EcoEnergy-Server`.
2. Haga clic en el botón superior **Connect**.
3. Utilice la pestaña **EC2 Instance Connect** y presione **Connect** para abrir una terminal directamente en el navegador web (sin necesidad de configurar clientes SSH locales).

---

### Paso 4: Clonar el Repositorio y Desplegar
Una vez dentro de la terminal de la instancia Ubuntu:

```bash
# 1. Clonar el repositorio del proyecto
git clone <URL_DE_SU_REPOSITORIO_GIT>
cd ecoenergy_fase1

# 2. Dar permisos de ejecución al script de despliegue automatizado
chmod +x deploy_aws.sh

# 3. Ejecutar el script de despliegue
./deploy_aws.sh
```

El script `deploy_aws.sh` se encargará automáticamente de:
- Actualizar el sistema e instalar Python 3, venv y git.
- Crear y activar el entorno virtual `.venv`.
- Instalar todas las dependencias de `requirements.txt`.
- Crear el archivo `.env` detectando la IP pública de AWS y configurando `ALLOWED_HOSTS`.
- Aplicar todas las migraciones de Django.
- Poblar la base de datos con **1.120+ registros de negocio** y los usuarios de prueba.

---

### Paso 5: Iniciar el Servidor de Aplicación
Para ejecutar el servidor accesible desde Internet:

```bash
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

*(Opcional para mantenerlo en segundo plano incluso si cierra la pestaña del navegador:)*
```bash
nohup python manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &
```

---

### Paso 6: Obtener la URL Pública para la Entrega
1. Vuelva a la consola de AWS EC2 y copie la **Public IPv4 address** (o el **Public IPv4 DNS**) de su instancia.
2. Su URL pública de entrega será:
   ```text
   http://<TU_IP_PUBLICA_AWS>:8000/
   ```
3. Compruebe en su navegador el acceso a:
   - Panel de inicio de sesión: `http://<TU_IP_PUBLICA_AWS>:8000/accounts/login/`
   - Dashboard: `http://<TU_IP_PUBLICA_AWS>:8000/dashboard/`
   - Django Admin: `http://<TU_IP_PUBLICA_AWS>:8000/admin/`

---

### Cuentas de Prueba para Demostración en Vivo

| Usuario | Contraseña | Rol / Contexto |
| :--- | :--- | :--- |
| **`admin`** | `AdminPassword123!` | Superadministrador Global |
| **`operador_norte`** | `OperadorNorte123!` | Operador / Editor (EcoIndustrias Norte S.A.) |
| **`lector_norte`** | `LectorNorte123!` | Lector / Consulta (EcoIndustrias Norte S.A.) |
| **`operador_sur`** | `OperadorSur123!` | Operador / Editor (EcoRetail Sur SpA) |
