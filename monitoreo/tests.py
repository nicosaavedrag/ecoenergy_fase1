import io
from decimal import Decimal
from datetime import timedelta
from PIL import Image

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone

from accounts.models import UserProfile, PasswordResetCode
from accounts.validators import ComplexityPasswordValidator
from monitoreo.models import (
    Organization,
    DeviceCategory,
    Supplier,
    EnergyTariff,
    Zone,
    Device,
    ConsumptionRecord,
    EnergyAlert,
    MaintenanceOrder,
    MonthlyZoneBudget,
)
from monitoreo.validators import validate_image_file


class FormativaUnidad2ComprehensiveTests(TestCase):
    """
    Suite exhaustiva de pruebas para la Evaluación Formativa Unidad II:
    1. 6 Tablas Maestras + 4 Tablas Operacionales.
    2. Carga >= 1.000 registros de negocio.
    3. Borrado lógico (Soft delete con deleted_at).
    4. Validación estricta de contraseña y código de 6 dígitos.
    5. Validación de imágenes con Pillow.
    6. Scoping y permisos (Admin, Operador, Lector).
    7. Paginación en sesión (5, 15, 30).
    8. Exportación a Excel (.xlsx).
    """

    @classmethod
    def setUpTestData(cls):
        call_command('poblar_datos', '--limpiar')

    def setUp(self):
        self.client = Client()

    # --------------------------------------------------------------------------
    # 1. MODELOS Y VOLUMEN (>= 1.000 REGISTROS)
    # --------------------------------------------------------------------------
    def test_modelos_minimos_y_volumen_superior_a_mil(self):
        # 6 Tablas Maestras
        self.assertGreaterEqual(Organization.objects.count(), 2)
        self.assertGreaterEqual(DeviceCategory.objects.count(), 4)
        self.assertGreaterEqual(Supplier.objects.count(), 3)
        self.assertGreaterEqual(EnergyTariff.objects.count(), 2)
        self.assertGreaterEqual(Zone.objects.count(), 8)
        self.assertGreaterEqual(Device.objects.count(), 16)

        # 4 Tablas Operativas
        self.assertGreaterEqual(ConsumptionRecord.objects.count(), 1000)
        self.assertGreaterEqual(EnergyAlert.objects.count(), 5)
        self.assertGreaterEqual(MaintenanceOrder.objects.count(), 10)
        self.assertGreaterEqual(MonthlyZoneBudget.objects.count(), 8)

        total_registros = (
            Organization.objects.count() + DeviceCategory.objects.count() +
            Supplier.objects.count() + EnergyTariff.objects.count() +
            Zone.objects.count() + Device.objects.count() +
            ConsumptionRecord.objects.count() + EnergyAlert.objects.count() +
            MaintenanceOrder.objects.count() + MonthlyZoneBudget.objects.count()
        )
        self.assertGreaterEqual(total_registros, 1000, "Debe superar los 1.000 registros de negocio.")

    # --------------------------------------------------------------------------
    # 2. BORRADO LÓGICO (SOFT DELETE)
    # --------------------------------------------------------------------------
    def test_borrado_logico_soft_delete(self):
        dev = Device.objects.first()
        dev_id = dev.id
        self.assertIsNone(dev.deleted_at)

        # Ejecutar delete()
        dev.delete()

        # Debe desaparecer del manager por defecto (objects)
        self.assertFalse(Device.objects.filter(id=dev_id).exists())

        # Pero debe seguir existiendo en all_objects con marca temporal
        deleted_dev = Device.all_objects.get(id=dev_id)
        self.assertIsNotNone(deleted_dev.deleted_at)
        self.assertTrue(deleted_dev.is_deleted)

    # --------------------------------------------------------------------------
    # 3. SEGURIDAD DE CONTRASEÑA (REGLA 10 CARACTERES + MAY + MIN + NUM + SÍMBOLO)
    # --------------------------------------------------------------------------
    def test_validador_complejidad_password(self):
        validator = ComplexityPasswordValidator(min_length=10)

        # Corta (< 10)
        with self.assertRaises(ValidationError):
            validator.validate("Short1!a")

        # Sin mayúscula
        with self.assertRaises(ValidationError):
            validator.validate("lowercase123!@#")

        # Sin minúscula
        with self.assertRaises(ValidationError):
            validator.validate("UPPERCASE123!@#")

        # Sin número
        with self.assertRaises(ValidationError):
            validator.validate("NoDigitsHere!@#")

        # Sin símbolo
        with self.assertRaises(ValidationError):
            validator.validate("NoSymbolPass1234")

        # Válida (>= 10, mayúscula, minúscula, número y símbolo)
        try:
            validator.validate("ValidPassword2026!")
        except ValidationError:
            self.fail("ValidPassword2026! debería ser aceptada.")

    # --------------------------------------------------------------------------
    # 4. RECUPERACIÓN DE CONTRASEÑA CON CÓDIGO DE 6 DÍGITOS
    # --------------------------------------------------------------------------
    def test_flujo_codigo_6_digitos_y_no_reutilizacion(self):
        user = User.objects.get(username='operador_norte')
        code_obj = PasswordResetCode.generate_code_for_user(user, validity_minutes=15)

        self.assertEqual(len(code_obj.code), 6)
        self.assertTrue(code_obj.code.isdigit())
        self.assertTrue(code_obj.is_valid())

        # Simular uso del código
        code_obj.is_used = True
        code_obj.save()

        # No puede ser reutilizado
        self.assertFalse(code_obj.is_valid())

    # --------------------------------------------------------------------------
    # 5. VALIDACIÓN DE IMAGEN CON PILLOW
    # --------------------------------------------------------------------------
    def test_validacion_imagen_real_pillow(self):
        # Crear imagen PNG real en memoria
        file_io = io.BytesIO()
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(file_io, format='PNG')
        file_io.seek(0)
        valid_uploaded_img = SimpleUploadedFile("test.png", file_io.read(), content_type="image/png")

        # No debe lanzar excepción
        try:
            validate_image_file(valid_uploaded_img)
        except ValidationError:
            self.fail("Imagen PNG válida no debería fallar.")

        # Archivo falso con extensión cambiada
        fake_file = SimpleUploadedFile("fake.png", b"ESTO NO ES UNA IMAGEN", content_type="image/png")
        with self.assertRaises(ValidationError):
            validate_image_file(fake_file)

        # Extensión no permitida
        exe_file = SimpleUploadedFile("virus.exe", b"executable", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_image_file(exe_file)

    # --------------------------------------------------------------------------
    # 6. SCOPING Y PERMISOS DE ROLES
    # --------------------------------------------------------------------------
    def test_scoping_operador_norte_vs_sur(self):
        self.client.login(username='operador_norte', password='OperadorNorte123!')
        response = self.client.get('/zones/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Planta de Fundición y Maestranza")
        self.assertNotContains(response, "Sala de Ventas Principal")

        self.client.login(username='operador_sur', password='OperadorSur123!')
        response_sur = self.client.get('/zones/')
        self.assertEqual(response_sur.status_code, 200)
        self.assertContains(response_sur, "Sala de Ventas Principal")
        self.assertNotContains(response_sur, "Planta de Fundición y Maestranza")

    def test_rol_lector_restringido(self):
        """Un usuario con rol VIEWER puede listar pero recibe 403 Forbidden al intentar crear."""
        self.client.login(username='lector_norte', password='LectorNorte123!')
        
        # Puede ver el listado
        resp_list = self.client.get('/zones/')
        self.assertEqual(resp_list.status_code, 200)

        # Intento de crear zona -> 403 Forbidden
        resp_create = self.client.post('/zones/new/', {'name': 'Zona No Autorizada'})
        self.assertEqual(resp_create.status_code, 403)

    # --------------------------------------------------------------------------
    # 7. PAGINACIÓN Y SESIÓN (5, 15, 30)
    # --------------------------------------------------------------------------
    def test_paginacion_persistida_en_sesion(self):
        self.client.login(username='admin', password='AdminPassword123!')
        
        # Petición solicitando 5 por página
        resp = self.client.get('/consumption/?page_size=5')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['page_obj']), 5)
        self.assertEqual(self.client.session.get('page_size'), 5)

        # Siguiente petición sin parámetro debe mantener los 5 gracias a la sesión
        resp2 = self.client.get('/consumption/')
        self.assertEqual(len(resp2.context['page_obj']), 5)

        # Valor no permitido (ej. 999) debe ser rechazado y normalizado
        self.client.get('/consumption/?page_size=999')
        # La sesión debe mantenerse en el valor seguro permitido
        self.assertIn(self.client.session.get('page_size'), [5, 15, 30])

    # --------------------------------------------------------------------------
    # 8. EXPORTACIÓN A EXCEL (.XLSX)
    # --------------------------------------------------------------------------
    def test_exportacion_excel_xlsx(self):
        self.client.login(username='admin', password='AdminPassword123!')
        resp = self.client.get('/consumption/?export=xlsx')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertTrue(resp['Content-Disposition'].startswith('attachment; filename="consumo_ecoenergy_'))
