from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import PasswordResetCode


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'})
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )


class RequestPasswordResetForm(forms.Form):
    METHOD_CHOICES = [
        ('whatsapp', '📱 Mensaje directo de WhatsApp al celular'),
        ('email', '✉️ Correo Electrónico'),
    ]

    username = forms.CharField(
        label="Nombre de Usuario",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: admin, operador_norte'}),
        help_text="Usuario registrado que requiere cambio de credenciales."
    )
    delivery_method = forms.ChoiceField(
        label="Canal de Notificación",
        choices=METHOD_CHOICES,
        initial='whatsapp',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    destination = forms.CharField(
        label="Número de Teléfono (WhatsApp) o Correo",
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: +56912345678 (WhatsApp) o usuario@ecoenergy.cl'
        }),
        help_text="Opcional. Si lo deja vacío, se utilizará el dato guardado en su perfil de usuario."
    )
    apikey = forms.CharField(
        label="API Key de CallMeBot (Opcional)",
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dejar vacío si ya está configurado en el servidor'
        }),
        help_text="Clave API entregada por el bot de WhatsApp (CallMeBot) para la demostración."
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not User.objects.filter(username=username).exists():
            raise ValidationError("No existe ningún usuario registrado con ese nombre.")
        return username



class VerifyResetCodeForm(forms.Form):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    code = forms.CharField(
        label="Código de 6 dígitos",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control text-center tracking-widest font-monospace fs-4', 'placeholder': '123456'})
    )
    new_password1 = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mínimo 10 caracteres'})
    )
    new_password2 = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita la nueva contraseña'})
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        code = cleaned_data.get('code')
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')

        if p1 and p2 and p1 != p2:
            self.add_error('new_password2', "Las contraseñas ingresadas no coinciden.")

        user = User.objects.filter(username=username).first()
        if not user:
            raise ValidationError("Usuario no encontrado.")

        # Validar el código de 6 dígitos
        reset_code = PasswordResetCode.objects.filter(user=user, code=code).first()
        if not reset_code:
            self.add_error('code', "El código ingresado es incorrecto.")
        elif not reset_code.is_valid():
            self.add_error('code', "El código ha expirado o ya fue utilizado anteriormente.")

        # Validar robustez de contraseña mediante validadores de Django configurados
        if p1 and p1 == p2:
            try:
                validate_password(p1, user=user)
            except ValidationError as error:
                self.add_error('new_password1', error)

        self.user_instance = user
        self.code_instance = reset_code
        return cleaned_data
