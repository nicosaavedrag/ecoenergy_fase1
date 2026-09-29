from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import PasswordResetCode
from .forms import LoginForm, RequestPasswordResetForm, VerifyResetCodeForm


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"¡Bienvenido, {user.first_name or user.username}!")
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, "Usuario o contraseña incorrectos.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('login')


def password_reset_request(request):
    """
    Paso 1: Solicita nombre de usuario y genera un código numérico de 6 dígitos.
    Para efectos de demostración en laboratorio se muestra el código en pantalla y en consola.
    """
    if request.method == 'POST':
        form = RequestPasswordResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            user = User.objects.get(username=username)
            code_obj = PasswordResetCode.generate_code_for_user(user)

            messages.info(
                request,
                f"Código generado para {user.username}: {code_obj.code} (Válido por 15 minutos)."
            )
            return redirect(f"/accounts/password-reset/verify/?username={username}")
    else:
        form = RequestPasswordResetForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_verify(request):
    """
    Paso 2: Valida el código de 6 dígitos y aplica la nueva contraseña segura.
    El código se invalida inmediatamente tras el uso exitoso.
    """
    initial_username = request.GET.get('username', '')

    if request.method == 'POST':
        form = VerifyResetCodeForm(request.POST)
        if form.is_valid():
            user = form.user_instance
            new_password = form.cleaned_data['new_password1']
            user.set_password(new_password)
            user.save()

            # Invalidar código
            code_obj = form.code_instance
            code_obj.is_used = True
            code_obj.save()

            messages.success(
                request,
                "Su contraseña ha sido actualizada con éxito. Ya puede iniciar sesión con su nueva clave."
            )
            return redirect('login')
    else:
        form = VerifyResetCodeForm(initial={'username': initial_username})

    return render(request, 'accounts/password_reset_verify.html', {'form': form})


@login_required
def profile_view(request):
    profile = getattr(request.user, 'profile', None)
    return render(request, 'accounts/profile.html', {'profile': profile})
