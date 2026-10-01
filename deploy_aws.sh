#!/bin/bash
# ==============================================================================
# Script de Despliegue Automatizado - AWS Academy (Ubuntu / Debian)
# EcoEnergy - Evaluación Formativa Unidad II
# ==============================================================================

set -e

echo "=== [1/6] Actualizando paquetes del sistema ==="
PYTHON_CMD="python3"
if command -v apt-get &> /dev/null; then
    # Entorno Ubuntu / Debian
    sudo apt-get update -y
    sudo apt-get install -y python3-pip python3-venv git libpq-dev
elif command -v dnf &> /dev/null; then
    # Entorno Amazon Linux 2023 / Fedora / RHEL
    sudo dnf update -y
    sudo dnf install -y python3.11 python3.11-pip git || sudo dnf install -y python3-pip git
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    fi
elif command -v yum &> /dev/null; then
    # Entorno Amazon Linux 2 / CentOS
    sudo yum update -y
    sudo yum install -y python3.11 python3.11-pip git || sudo yum install -y python3-pip git
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    fi
else
    echo "Advertencia: No se detectó un gestor de paquetes soportado (apt/dnf/yum). Continuando..."
fi

echo "=== [2/6] Configurando entorno virtual ($PYTHON_CMD) ==="
if [ ! -d ".venv" ] || [ ! -f ".venv/bin/activate" ]; then
    rm -rf .venv
    $PYTHON_CMD -m venv .venv
fi
source .venv/bin/activate


echo "=== [3/6] Instalando dependencias ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== [4/6] Configurando archivo .env ==="
if [ ! -f ".env" ]; then
    cp .env.example .env
    # Permitir la IP pública de AWS y localhost
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com || echo "*")
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=127.0.0.1,localhost,$PUBLIC_IP,*/g" .env
fi

echo "=== [5/6] Ejecutando migraciones y carga de datos reproducibles (>= 1.000 registros) ==="
python manage.py migrate
python manage.py poblar_datos --limpiar

echo "=== [6/6] Creando directorio para archivos multimedia ==="
mkdir -p media/devices

echo "=============================================================================="
echo " [OK] Despliegue completado con éxito."
echo " Para iniciar el servidor accesible públicamente en el puerto 8000, ejecute:"
echo "    source .venv/bin/activate"
echo "    python manage.py runserver 0.0.0.0:8000"
echo " (Recuerde habilitar el puerto 8000 en el Security Group de su instancia EC2)"
echo "=============================================================================="
