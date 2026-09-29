from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from .validators import validate_image_file


# ==============================================================================
# BORRADO LÓGICO (SOFT DELETE FRAMEWORK)
# ==============================================================================

class SoftDeleteQuerySet(models.QuerySet):
    """
    QuerySet personalizado para gestionar el borrado lógico.
    """
    def delete(self):
        """Sobrescribe el borrado masivo para asignar deleted_at en lugar de eliminar físicamente."""
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        """Eliminación física real en caso de ser requerida por procesos de mantenimiento."""
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """
    Manager por defecto que excluye automáticamente los registros eliminados lógicamente.
    """
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)


class SoftDeleteModel(models.Model):
    """
    Clase base abstracta que implementa el borrado lógico mediante deleted_at.
    """
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name="Fecha de Borrado Lógico")

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])

    @property
    def is_deleted(self):
        return self.deleted_at is not None


# ==============================================================================
# TABLAS MAESTRAS (MASTER TABLES - 6 MODELOS)
# ==============================================================================

class Organization(SoftDeleteModel):
    """
    Master Table 1: Organization
    Representa a cada empresa cliente del sistema multi-tenant EcoEnergy.
    """
    name = models.CharField(max_length=150, verbose_name="Nombre de la Organización")
    tax_id = models.CharField(max_length=20, unique=True, verbose_name="RUT / ID Tributario")
    address = models.CharField(max_length=255, verbose_name="Dirección Comercial")
    contact_email = models.EmailField(verbose_name="Email de Contacto")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    is_active = models.BooleanField(default=True, verbose_name="¿Activa?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    class Meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.tax_id})"


class DeviceCategory(SoftDeleteModel):
    """
    Master Table 2: DeviceCategory
    Clasificación técnica de los equipos de consumo energético.
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_critical = models.BooleanField(
        default=False,
        verbose_name="¿Es Crítica?",
        help_text="Define si la categoría requiere atención prioritaria ante fallas."
    )

    class Meta:
        verbose_name = "Categoría de Dispositivo"
        verbose_name_plural = "Categorías de Dispositivos"
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(SoftDeleteModel):
    """
    Master Table 3: Supplier
    Empresas proveedoras, fabricantes o de soporte técnico de equipamiento.
    """
    name = models.CharField(max_length=150, verbose_name="Nombre del Proveedor")
    contact_person = models.CharField(max_length=120, verbose_name="Persona de Contacto")
    email = models.EmailField(verbose_name="Email del Proveedor")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    contract_number = models.CharField(max_length=50, blank=True, verbose_name="Número de Contrato / Convenio")

    class Meta:
        verbose_name = "Proveedor de Equipos"
        verbose_name_plural = "Proveedores de Equipos"
        ordering = ['name']

    def __str__(self):
        return self.name


class EnergyTariff(SoftDeleteModel):
    """
    Master Table 4: EnergyTariff
    Estructura tarifaria de suministro eléctrico aplicable a cada organización.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='tariffs',
        verbose_name="Organización"
    )
    name = models.CharField(max_length=100, verbose_name="Nombre de Tarifa")
    cost_per_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Costo Base por kWh (CLP)"
    )
    peak_cost_per_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Costo Horario Punta (CLP)"
    )
    currency = models.CharField(max_length=10, default="CLP", verbose_name="Moneda")
    is_active = models.BooleanField(default=True, verbose_name="¿Tarifa Vigente?")

    class Meta:
        verbose_name = "Tarifa Energética"
        verbose_name_plural = "Tarifas Energéticas"
        ordering = ['organization__name', 'name']

    def clean(self):
        if self.cost_per_kwh is not None and self.cost_per_kwh < 0:
            raise ValidationError({'cost_per_kwh': 'El costo base no puede ser negativo.'})
        if self.peak_cost_per_kwh is not None and self.peak_cost_per_kwh < 0:
            raise ValidationError({'peak_cost_per_kwh': 'El costo horario punta no puede ser negativo.'})

    def __str__(self):
        return f"{self.name} - {self.organization.name} (${self.cost_per_kwh}/kWh)"


class Zone(SoftDeleteModel):
    """
    Master Table 5: Zone
    Áreas físicas o sectores de consumo pertenecientes a una organización.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='zones',
        verbose_name="Organización"
    )
    name = models.CharField(max_length=120, verbose_name="Nombre de la Zona")
    monthly_limit_kwh = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Límite Mensual (kWh)",
        help_text="Umbral máximo permitido antes de disparar alertas de consumo."
    )
    floor_area_sqm = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal("100.00"),
        verbose_name="Superficie (m²)"
    )
    responsible_person = models.CharField(max_length=120, blank=True, verbose_name="Responsable de Área")
    is_active = models.BooleanField(default=True, verbose_name="¿Zona Operativa?")

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ['organization__name', 'name']

    def clean(self):
        if self.monthly_limit_kwh is not None and self.monthly_limit_kwh <= 0:
            raise ValidationError({
                'monthly_limit_kwh': 'El límite mensual de consumo debe ser estrictamente mayor a 0 kWh.'
            })
        if self.floor_area_sqm is not None and self.floor_area_sqm <= 0:
            raise ValidationError({
                'floor_area_sqm': 'La superficie debe ser un valor positivo mayor a 0 m².'
            })

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class Device(SoftDeleteModel):
    """
    Master Table 6: Device
    Equipos consumidores de energía instalados en una Zona.
    Incluye campo de imagen con validación Pillow y control de tamaño.
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Activo'),
        ('MAINTENANCE', 'En Mantenimiento'),
        ('INACTIVE', 'Inactivo'),
    ]

    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name="Zona Asignada"
    )
    category = models.ForeignKey(
        DeviceCategory,
        on_delete=models.PROTECT,
        related_name='devices',
        verbose_name="Categoría"
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devices',
        verbose_name="Proveedor Asociado"
    )
    name = models.CharField(max_length=120, verbose_name="Nombre del Dispositivo")
    serial_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número de Serie / Código"
    )
    nominal_power_kw = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Potencia Nominal (kW)"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Estado Operativo"
    )
    image = models.ImageField(
        upload_to='devices/',
        blank=True,
        null=True,
        validators=[validate_image_file],
        verbose_name="Fotografía o Ficha Técnica",
        help_text="Formatos: .jpg, .png, .webp. Máximo 2 MB."
    )
    installation_date = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Instalación"
    )

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"
        ordering = ['name']

    def clean(self):
        if self.status == 'ACTIVE' and (self.nominal_power_kw is None or self.nominal_power_kw <= 0):
            raise ValidationError({
                'nominal_power_kw': 'Un dispositivo activo debe registrar una potencia nominal mayor a 0 kW.'
            })

    def __str__(self):
        return f"{self.name} [{self.serial_number}]"


# ==============================================================================
# TABLAS OPERACIONALES (OPERATIONAL TABLES - 4 MODELOS)
# ==============================================================================

class ConsumptionRecord(SoftDeleteModel):
    """
    Operational Table 1: ConsumptionRecord
    Mediciones periódicas o telemetría de consumo eléctrico tomadas por dispositivo.
    """
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='consumption_records',
        verbose_name="Dispositivo"
    )
    recorded_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y Hora de Medición"
    )
    consumption_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Consumo Eléctrico (kWh)"
    )
    average_voltage = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Voltaje Promedio (V)"
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Observaciones Operacionales"
    )

    class Meta:
        verbose_name = "Registro de Consumo"
        verbose_name_plural = "Registros de Consumo"
        ordering = ['-recorded_at']

    def clean(self):
        if self.consumption_kwh is not None and self.consumption_kwh < 0:
            raise ValidationError({
                'consumption_kwh': 'El consumo eléctrico registrado no puede ser negativo.'
            })
        if self.recorded_at and self.recorded_at > timezone.now():
            raise ValidationError({
                'recorded_at': 'La fecha y hora de la medición no puede ser futura.'
            })

    def __str__(self):
        return f"{self.device.name} - {self.consumption_kwh} kWh ({self.recorded_at.strftime('%d/%m/%Y %H:%M')})"


class EnergyAlert(SoftDeleteModel):
    """
    Operational Table 2: EnergyAlert
    Registro de incidencias, sobreconsumos y anomalías en equipos o zonas.
    """
    SEVERITY_CHOICES = [
        ('LOW', 'Baja'),
        ('MEDIUM', 'Media'),
        ('HIGH', 'Alta'),
        ('CRITICAL', 'Crítica'),
    ]

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='alerts',
        verbose_name="Dispositivo Afectado"
    )
    triggered_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y Hora de Detección"
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        default='MEDIUM',
        verbose_name="Nivel de Severidad"
    )
    message = models.TextField(verbose_name="Mensaje de la Alerta")
    is_resolved = models.BooleanField(default=False, verbose_name="¿Resuelta?")
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Resolución"
    )

    class Meta:
        verbose_name = "Alerta de Consumo"
        verbose_name_plural = "Alertas de Consumo"
        ordering = ['-triggered_at']

    def clean(self):
        if self.is_resolved and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif not self.is_resolved:
            self.resolved_at = None

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.device.name}: {self.message[:40]}"


class MaintenanceOrder(SoftDeleteModel):
    """
    Operational Table 3: MaintenanceOrder
    Órdenes de mantenimiento preventivo y correctivo para los dispositivos.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('IN_PROGRESS', 'En Proceso'),
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada'),
    ]

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='maintenance_orders',
        verbose_name="Dispositivo"
    )
    title = models.CharField(max_length=150, verbose_name="Título de la Orden")
    scheduled_date = models.DateField(verbose_name="Fecha Programada")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Estado de la Orden"
    )
    technician_notes = models.TextField(blank=True, verbose_name="Notas del Técnico")
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Costo de Intervención (CLP)"
    )

    class Meta:
        verbose_name = "Orden de Mantenimiento"
        verbose_name_plural = "Órdenes de Mantenimiento"
        ordering = ['-scheduled_date']

    def clean(self):
        if self.cost is not None and self.cost < 0:
            raise ValidationError({'cost': 'El costo de la orden no puede ser negativo.'})

    def __str__(self):
        return f"Orden #{self.id}: {self.title} ({self.device.name})"


class MonthlyZoneBudget(SoftDeleteModel):
    """
    Operational Table 4: MonthlyZoneBudget
    Control presupuestario y balance energético mensual planificado vs real por zona.
    """
    zone = models.ForeignKey(
        Zone,
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name="Zona"
    )
    year = models.PositiveIntegerField(verbose_name="Año")
    month = models.PositiveIntegerField(verbose_name="Mes (1-12)")
    budgeted_kwh = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Presupuesto Mensual (kWh)"
    )
    actual_kwh = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Consumo Real Acumulado (kWh)"
    )
    is_closed = models.BooleanField(default=False, verbose_name="¿Mes Cerrado?")

    class Meta:
        verbose_name = "Presupuesto Mensual de Zona"
        verbose_name_plural = "Presupuestos Mensuales de Zonas"
        unique_together = ('zone', 'year', 'month')
        ordering = ['-year', '-month']

    def clean(self):
        if not (1 <= self.month <= 12):
            raise ValidationError({'month': 'El mes debe estar comprendido entre 1 y 12.'})
        if self.budgeted_kwh is not None and self.budgeted_kwh <= 0:
            raise ValidationError({'budgeted_kwh': 'El presupuesto asignado debe ser mayor a 0 kWh.'})

    def __str__(self):
        return f"{self.zone.name} - {self.month:02d}/{self.year} (Meta: {self.budgeted_kwh} kWh)"
