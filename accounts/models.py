import random
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """
    Extensión del usuario estándar de Django para soporte de roles y scoping multi-empresa.
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('OPERATOR', 'Operador / Editor'),
        ('VIEWER', 'Lector / Consulta'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Usuario")
    # Referenciamos a monitoreo.Organization como string para evitar import circular
    organization = models.ForeignKey(
        'monitoreo.Organization',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_profiles',
        verbose_name="Organización Asignada",
        help_text="Organización para scoping. Vacío indica Administrador Global con acceso irrestricto."
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OPERATOR', verbose_name="Rol en el Sistema")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Teléfono")

    class Meta:
        verbose_name = "Perfil de Usuario"
        verbose_name_plural = "Perfiles de Usuario"

    def __str__(self):
        org_name = self.organization.name if self.organization else "Acceso Global"
        return f"{self.user.username} ({self.get_role_display()} - {org_name})"


class PasswordResetCode(models.Model):
    """
    Códigos numéricos de 6 dígitos para recuperación de contraseña:
    - Generación aleatoria segura de 6 dígitos.
    - Vigencia temporal (15 minutos).
    - Un solo uso (no reutilizable tras recuperación exitosa).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_codes', verbose_name="Usuario")
    code = models.CharField(max_length=6, verbose_name="Código de 6 dígitos")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    expires_at = models.DateTimeField(verbose_name="Fecha de Expiración")
    is_used = models.BooleanField(default=False, verbose_name="¿Fue Utilizado?")

    class Meta:
        verbose_name = "Código de Recuperación"
        verbose_name_plural = "Códigos de Recuperación"
        ordering = ['-created_at']

    @classmethod
    def generate_code_for_user(cls, user, validity_minutes=15):
        """Genera un código numérico aleatorio de 6 dígitos y marca los anteriores como usados."""
        cls.objects.filter(user=user, is_used=False).update(is_used=True)
        numeric_code = f"{random.randint(100000, 999999)}"
        expiration = timezone.now() + timedelta(minutes=validity_minutes)
        return cls.objects.create(user=user, code=numeric_code, expires_at=expiration)

    def is_valid(self):
        """Verifica si el código aún no ha sido utilizado y no ha expirado."""
        return not self.is_used and timezone.now() <= self.expires_at

    def __str__(self):
        return f"Código {self.code} para {self.user.username} (Usado: {self.is_used})"
