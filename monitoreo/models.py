from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


# ==============================================================================
# TABLAS MAESTRAS (Entidades Base / Catálogos)
# ==============================================================================

class Organizacion(models.Model):
    """
    Tabla Maestra 1: Representa la empresa u organización cliente.
    Permite el scoping multi-empresa/multi-organización exigido por la rúbrica.
    """
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Organización")
    rut = models.CharField(max_length=20, unique=True, verbose_name="RUT / Identificador")
    direccion = models.CharField(max_length=255, verbose_name="Dirección")
    email_contacto = models.EmailField(verbose_name="Email de Contacto")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")
    activa = models.BooleanField(default=True, verbose_name="¿Activa?")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")

    class Meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.rut})"


class CategoriaDispositivo(models.Model):
    """
    Tabla Maestra 2: Catálogo de categorías técnicas de equipos de consumo.
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    es_critica = models.BooleanField(
        default=False,
        verbose_name="¿Categoría Crítica?",
        help_text="Indica si los equipos de esta categoría requieren monitoreo prioritario."
    )

    class Meta:
        verbose_name = "Categoría de Dispositivo"
        verbose_name_plural = "Categorías de Dispositivos"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Zona(models.Model):
    """
    Tabla Maestra 3: Áreas físicas o dependencias asociadas a una Organización.
    """
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
        related_name='zonas',
        verbose_name="Organización"
    )
    nombre = models.CharField(max_length=120, verbose_name="Nombre de la Zona")
    limite_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Límite Consumo (kWh)",
        help_text="Umbral máximo mensual permitido antes de generar alertas."
    )
    descripcion = models.TextField(blank=True, verbose_name="Descripción de la Zona")
    responsable = models.CharField(max_length=120, blank=True, verbose_name="Responsable")
    activa = models.BooleanField(default=True, verbose_name="¿Zona Operativa?")

    class Meta:
        verbose_name = "Zona"
        verbose_name_plural = "Zonas"
        ordering = ['organizacion__nombre', 'nombre']

    def clean(self):
        """
        Validación controlada de negocio para Zona.
        """
        if self.limite_kwh is not None and self.limite_kwh <= 0:
            raise ValidationError({
                'limite_kwh': 'El límite de consumo debe ser un valor positivo estrictamente mayor a 0 kWh.'
            })

    def __str__(self):
        return f"{self.nombre} ({self.organizacion.nombre})"


class Dispositivo(models.Model):
    """
    Tabla Maestra 4: Equipos consumidores de energía eléctrica instalados en una Zona.
    """
    ESTADO_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('INACTIVO', 'Inactivo'),
    ]

    zona = models.ForeignKey(
        Zona,
        on_delete=models.CASCADE,
        related_name='dispositivos',
        verbose_name="Zona"
    )
    categoria = models.ForeignKey(
        CategoriaDispositivo,
        on_delete=models.PROTECT,
        related_name='dispositivos',
        verbose_name="Categoría"
    )
    nombre = models.CharField(max_length=120, verbose_name="Nombre del Dispositivo")
    codigo_inventario = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Código de Inventario"
    )
    potencia_nominal_kw = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name="Potencia Nominal (kW)"
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='ACTIVO',
        verbose_name="Estado Operativo"
    )
    fecha_instalacion = models.DateField(
        default=timezone.now,
        verbose_name="Fecha de Instalación"
    )

    class Meta:
        verbose_name = "Dispositivo"
        verbose_name_plural = "Dispositivos"
        ordering = ['nombre']

    def clean(self):
        """
        Validación controlada de negocio para Dispositivo:
        Un dispositivo marcado como 'ACTIVO' debe tener una potencia nominal > 0.
        """
        if self.estado == 'ACTIVO' and (self.potencia_nominal_kw is None or self.potencia_nominal_kw <= 0):
            raise ValidationError({
                'potencia_nominal_kw': 'Un dispositivo activo debe registrar una potencia nominal mayor a 0 kW.'
            })

    def __str__(self):
        return f"{self.nombre} [{self.codigo_inventario}]"


class PerfilUsuario(models.Model):
    """
    Tabla de Extensión de Usuario:
    Asocia un usuario de Django a una Organización para habilitar el scoping de seguridad.
    """
    ROL_CHOICES = [
        ('ADMIN_GLOBAL', 'Administrador Global'),
        ('ADMIN_ORG', 'Administrador de Organización'),
        ('OPERADOR', 'Operador de Monitoreo'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name="Usuario"
    )
    organizacion = models.ForeignKey(
        Organizacion,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='usuarios_perfil',
        verbose_name="Organización Asignada",
        help_text="Organización para scoping. Dejar en blanco si es Administrador Global."
    )
    rol = models.CharField(
        max_length=30,
        choices=ROL_CHOICES,
        default='OPERADOR',
        verbose_name="Rol en el Sistema"
    )
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono de Contacto")

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuarios"

    def __str__(self):
        org_nombre = self.organizacion.nombre if self.organizacion else "Acceso Global"
        return f"{self.user.username} ({self.get_rol_display()} - {org_nombre})"


# ==============================================================================
# TABLAS OPERATIVAS (Transaccionales / Eventos)
# ==============================================================================

class RegistroConsumo(models.Model):
    """
    Tabla Operativa 1: Mediciones periódicas o lecturas operativas de consumo eléctrico.
    """
    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.CASCADE,
        related_name='registros_consumo',
        verbose_name="Dispositivo"
    )
    fecha_hora = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y Hora de Medición"
    )
    consumo_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Consumo Registrado (kWh)"
    )
    voltaje_promedio = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Voltaje Promedio (V)"
    )
    observacion = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Observación Operativa"
    )

    class Meta:
        verbose_name = "Registro de Consumo"
        verbose_name_plural = "Registros de Consumo"
        ordering = ['-fecha_hora']

    def clean(self):
        """
        Validación controlada de negocio para RegistroConsumo:
        El consumo no puede ser negativo y la fecha no puede ser futura.
        """
        if self.consumo_kwh is not None and self.consumo_kwh < 0:
            raise ValidationError({
                'consumo_kwh': 'El consumo eléctrico registrado no puede ser un valor negativo.'
            })
        if self.fecha_hora and self.fecha_hora > timezone.now():
            raise ValidationError({
                'fecha_hora': 'La fecha y hora de la medición no puede ser en el futuro.'
            })

    def __str__(self):
        return f"{self.dispositivo.nombre} - {self.consumo_kwh} kWh ({self.fecha_hora.strftime('%d/%m/%Y %H:%M')})"


class AlertaConsumo(models.Model):
    """
    Tabla Operativa 2: Registro de incidencias, sobreconsumos y alertas operativas.
    """
    SEVERIDAD_CHOICES = [
        ('BAJA', 'Baja'),
        ('MEDIA', 'Media'),
        ('ALTA', 'Alta'),
        ('CRITICA', 'Crítica'),
    ]

    dispositivo = models.ForeignKey(
        Dispositivo,
        on_delete=models.CASCADE,
        related_name='alertas',
        verbose_name="Dispositivo Afectado"
    )
    fecha_hora = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha y Hora de la Alerta"
    )
    nivel = models.CharField(
        max_length=20,
        choices=SEVERIDAD_CHOICES,
        default='MEDIA',
        verbose_name="Nivel de Severidad"
    )
    mensaje = models.TextField(verbose_name="Detalle de la Alerta")
    resuelta = models.BooleanField(default=False, verbose_name="¿Resuelta?")
    resuelta_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha y Hora de Resolución"
    )

    class Meta:
        verbose_name = "Alerta de Consumo"
        verbose_name_plural = "Alertas de Consumo"
        ordering = ['-fecha_hora']

    def clean(self):
        """
        Validación controlada de negocio para AlertaConsumo:
        Si se marca como resuelta y no tiene fecha, se asigna automáticamente.
        """
        if self.resuelta and not self.resuelta_en:
            self.resuelta_en = timezone.now()
        elif not self.resuelta:
            self.resuelta_en = None

    def __str__(self):
        return f"[{self.nivel}] {self.dispositivo.nombre}: {self.mensaje[:40]}"
