import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexityPasswordValidator:
    """
    Validador estricto de complejidad para contraseñas de la Evaluación Formativa II:
    - Mínimo 10 caracteres.
    - Al menos una letra mayúscula.
    - Al menos una letra minúscula.
    - Al menos un número.
    - Al menos un carácter especial (!@#$%^&*(),.?":{}|<>_+-).
    """
    def __init__(self, min_length=10):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _(f"La contraseña debe contener al menos {self.min_length} caracteres."),
                code='password_too_short',
            )
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("La contraseña debe incluir al menos una letra mayúscula."),
                code='password_no_upper',
            )
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("La contraseña debe incluir al menos una letra minúscula."),
                code='password_no_lower',
            )
        if not re.search(r'\d', password):
            raise ValidationError(
                _("La contraseña debe incluir al menos un dígito numérico."),
                code='password_no_digit',
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_+~`\-=\[\]\\/]', password):
            raise ValidationError(
                _("La contraseña debe incluir al menos un carácter especial (ej. !@#$%&*_-)."),
                code='password_no_symbol',
            )

    def get_help_text(self):
        return _(
            "Su contraseña debe tener al menos 10 caracteres e incluir letras mayúsculas, "
            "minúsculas, números y al menos un símbolo o carácter especial."
        )
