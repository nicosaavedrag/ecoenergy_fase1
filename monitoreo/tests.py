from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils import timezone
from .models import (
    Organizacion,
    CategoriaDispositivo,
    Zona,
    Dispositivo,
    RegistroConsumo,
    AlertaConsumo,
)


class EvaluacionSumativa2Tests(TestCase):
    """
    Pruebas automatizadas para verificar el cumplimiento íntegro de la Evaluación Sumativa II:
    1. Carga de datos reproducibles (seed / management command).
    2. Modelos maestros y operativos.
    3. Validaciones de negocio controladas con clean().
    4. Seguridad y Scoping multi-organización en Django Admin.
    """

    def setUp(self):
        call_command('poblar_datos', '--limpiar')
        self.client = Client()

    def test_modelos_y_datos_cargados(self):
        """Verifica que existan al menos 4 tablas maestras y 2 operativas con datos."""
        # Tablas Maestras
        self.assertGreaterEqual(Organizacion.objects.count(), 2)
        self.assertGreaterEqual(CategoriaDispositivo.objects.count(), 3)
        self.assertGreaterEqual(Zona.objects.count(), 4)
        self.assertGreaterEqual(Dispositivo.objects.count(), 6)

        # Tablas Operativas
        self.assertGreaterEqual(RegistroConsumo.objects.count(), 5)
        self.assertGreaterEqual(AlertaConsumo.objects.count(), 2)

    def test_validacion_controlada_zona(self):
        """clean() de Zona debe rechazar un límite <= 0."""
        org = Organizacion.objects.first()
        zona_invalida = Zona(
            organizacion=org,
            nombre="Zona Error",
            limite_kwh=Decimal("-10.00")
        )
        with self.assertRaises(ValidationError) as ctx:
            zona_invalida.clean()
        self.assertIn('limite_kwh', ctx.exception.message_dict)

    def test_validacion_controlada_dispositivo(self):
        """clean() de Dispositivo activo debe rechazar potencia <= 0."""
        zona = Zona.objects.first()
        cat = CategoriaDispositivo.objects.first()
        disp_invalido = Dispositivo(
            zona=zona,
            categoria=cat,
            nombre="Motor Fallido",
            codigo_inventario="ERR-001",
            potencia_nominal_kw=Decimal("0.00"),
            estado="ACTIVO"
        )
        with self.assertRaises(ValidationError) as ctx:
            disp_invalido.clean()
        self.assertIn('potencia_nominal_kw', ctx.exception.message_dict)

    def test_validacion_controlada_registro_consumo(self):
        """clean() de RegistroConsumo debe rechazar consumo negativo y fechas futuras."""
        disp = Dispositivo.objects.first()
        # Consumo negativo
        reg_negativo = RegistroConsumo(
            dispositivo=disp,
            fecha_hora=timezone.now(),
            consumo_kwh=Decimal("-5.00")
        )
        with self.assertRaises(ValidationError) as ctx:
            reg_negativo.clean()
        self.assertIn('consumo_kwh', ctx.exception.message_dict)

        # Fecha futura
        reg_futuro = RegistroConsumo(
            dispositivo=disp,
            fecha_hora=timezone.now() + timedelta(days=2),
            consumo_kwh=Decimal("15.00")
        )
        with self.assertRaises(ValidationError) as ctx:
            reg_futuro.clean()
        self.assertIn('fecha_hora', ctx.exception.message_dict)

    def test_scoping_superusuario_ve_todo(self):
        """El superadministrador debe ver los datos de todas las organizaciones en el Admin."""
        self.client.login(username='admin', password='AdminPassword123!')
        response = self.client.get('/admin/monitoreo/zona/')
        self.assertEqual(response.status_code, 200)
        # Debe contener zonas de Norte y de Sur
        self.assertContains(response, "Planta de Fundición y Maestranza")
        self.assertContains(response, "Sala de Ventas Principal")

    def test_scoping_operador_norte_aislado(self):
        """El operador norte SOLO ve zonas y dispositivos de EcoIndustrias Norte."""
        self.client.login(username='operador_norte', password='OperadorNorte123!')
        
        # Zonas
        response = self.client.get('/admin/monitoreo/zona/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planta de Fundición y Maestranza")
        self.assertNotContains(response, "Sala de Ventas Principal")
        self.assertNotContains(response, "Cámaras de Congelado")

        # Dispositivos
        response_disp = self.client.get('/admin/monitoreo/dispositivo/')
        self.assertEqual(response_disp.status_code, 200)
        self.assertContains(response_disp, "Torno CNC Haas ST-30")
        self.assertNotContains(response_disp, "Compresor Bitzer Doble Etapa")

    def test_scoping_operador_sur_aislado(self):
        """El operador sur SOLO ve zonas y dispositivos de EcoRetail Sur."""
        self.client.login(username='operador_sur', password='OperadorSur123!')
        
        # Zonas
        response = self.client.get('/admin/monitoreo/zona/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sala de Ventas Principal")
        self.assertNotContains(response, "Planta de Fundición y Maestranza")
        self.assertNotContains(response, "Línea de Ensamble Automatizado")

        # Dispositivos
        response_disp = self.client.get('/admin/monitoreo/dispositivo/')
        self.assertEqual(response_disp.status_code, 200)
        self.assertContains(response_disp, "Compresor Bitzer Doble Etapa")
        self.assertNotContains(response_disp, "Torno CNC Haas ST-30")
