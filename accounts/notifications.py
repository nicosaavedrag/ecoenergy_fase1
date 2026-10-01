import logging
import urllib.parse
import urllib.request
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_whatsapp_message(phone_number, text, apikey=None):
    """
    Despacha un mensaje de WhatsApp a través de la API gratuita de CallMeBot.
    Compatible de forma nativa con Windows, Linux Ubuntu (AWS EC2) y macOS.
    No requiere librerías externas adicionales (usa urllib estándar).
    """
    key = apikey or getattr(settings, 'CALLMEBOT_API_KEY', '')
    if not key:
        return False, "No se ha configurado la API Key de CallMeBot (configure CALLMEBOT_API_KEY en .env o en el formulario)."

    # Limpiar formato de teléfono: conservar dígitos y eliminar espacios, guiones o signos
    clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
    if clean_phone.startswith("+"):
        clean_phone = clean_phone[1:]

    encoded_text = urllib.parse.quote(text)
    url = f"https://api.callmebot.com/whatsapp.php?phone={clean_phone}&text={encoded_text}&apikey={key}"

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (EcoEnergy-Security-Bot/1.0)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            response_body = response.read().decode('utf-8', errors='ignore')
            if status_code == 200:
                return True, "Mensaje enviado exitosamente a WhatsApp."
            return False, f"Respuesta de CallMeBot (HTTP {status_code}): {response_body}"
    except Exception as e:
        logger.warning(f"Error al enviar mensaje vía WhatsApp: {e}")
        return False, f"Fallo de conexión con WhatsApp: {str(e)}"


def send_recovery_code(user, code, method='whatsapp', destination=None, apikey=None):
    """
    Envía el código de 6 dígitos mediante el canal seleccionado (WhatsApp o Correo).
    Garantiza además la impresión en consola como red de seguridad para demostraciones en vivo.
    """
    # 1. Red de seguridad: Impresión destacada en la terminal del servidor (compatible con CP1252 y UTF-8)
    print("\n" + "=" * 68)
    print("[ECOENERGY SEGURIDAD - DEMOSTRACION 2FA]")
    print(f"   * Usuario: {user.username}")
    print(f"   * CODIGO DE 6 DIGITOS: >>> {code} <<< (Vigencia: 15 minutos)")
    print(f"   * Canal seleccionado: {method.upper()}")
    if destination:
        print(f"   * Destino: {destination}")
    print("=" * 68 + "\n")


    message_text = (
        f"EcoEnergy Seguridad:\n"
        f"Su código de verificación para cambio de clave es: {code}\n\n"
        f"Válido por 15 minutos. Ingréselo en la plataforma para continuar."
    )

    if method == 'whatsapp':
        # Prioridad de teléfono: destino en formulario -> UserProfile.phone -> .env
        profile = getattr(user, 'profile', None)
        target_phone = destination or (profile.phone if profile else '') or getattr(settings, 'CALLMEBOT_PHONE', '')
        
        if not target_phone:
            return False, "No se especificó un número de teléfono para el envío de WhatsApp."

        success, msg = send_whatsapp_message(target_phone, message_text, apikey=apikey)
        return success, f"WhatsApp ({target_phone}): {msg}"

    else:
        # Envío por correo electrónico
        target_email = destination or user.email or 'admin@ecoenergy.cl'
        try:
            send_mail(
                subject="EcoEnergy - Código de Recuperación de Contraseña",
                message=(
                    f"Estimado/a {user.first_name or user.username},\n\n"
                    f"Se ha solicitado el restablecimiento de su contraseña en la plataforma EcoEnergy.\n\n"
                    f"Su código de seguridad de 6 dígitos es: {code}\n\n"
                    f"Este código es de un solo uso y expirará en 15 minutos.\n"
                    f"Si usted no realizó esta solicitud, puede ignorar este mensaje.\n\n"
                    f"Atentamente,\nEquipo de Seguridad y Monitoreo EcoEnergy"
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@ecoenergy.cl'),
                recipient_list=[target_email],
                fail_silently=False,
            )
            return True, f"Correo electrónico despachado a {target_email}."
        except Exception as e:
            return False, f"Fallo al despachar correo electrónico: {str(e)}"
