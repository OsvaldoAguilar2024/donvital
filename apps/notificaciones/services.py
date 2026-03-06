"""
DON VITAL - Servicios de notificación (SMS, Push, WhatsApp)
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def normalizar_telefono(telefono: str) -> str:
    """Asegura formato E.164 para Colombia."""
    telefono = telefono.strip().replace(' ', '').replace('-', '')
    if telefono.startswith('00'):
        telefono = '+' + telefono[2:]
    elif telefono.startswith('57') and len(telefono) == 12:
        telefono = '+' + telefono
    elif telefono.startswith('3') and len(telefono) == 10:
        telefono = '+57' + telefono
    elif not telefono.startswith('+'):
        telefono = '+57' + telefono
    return telefono


def enviar_sms_otp(telefono: str, codigo: str) -> bool:
    """Envía OTP por SMS via Twilio. En DEBUG muestra en consola."""
    telefono = normalizar_telefono(telefono)
    mensaje = f'Don Vital: Tu código de acceso es {codigo}. Válido por 10 minutos. No lo compartas.'

    if settings.DEBUG and not settings.TWILIO_ACCOUNT_SID:
        logger.info(f'[DEBUG SMS] Para {telefono}: {mensaje}')
        print(f'\n🔐 CÓDIGO OTP para {telefono}: {codigo}\n')
        return True

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=mensaje,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=telefono
        )
        logger.info(f'SMS OTP enviado a {telefono}')
        return True
    except Exception as e:
        logger.error(f'Error enviando SMS OTP a {telefono}: {e}')
        return False


def enviar_sms(telefono: str, mensaje: str) -> bool:
    """Envía SMS genérico."""
    telefono = normalizar_telefono(telefono)
    if settings.DEBUG and not settings.TWILIO_ACCOUNT_SID:
        logger.info(f'[DEBUG SMS] Para {telefono}: {mensaje}')
        print(f'\n📱 SMS para {telefono}: {mensaje}\n')
        return True

    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=mensaje,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=telefono
        )
        return True
    except Exception as e:
        logger.error(f'Error SMS a {telefono}: {e}')
        return False


def enviar_push(usuario, titulo: str, cuerpo: str, url: str = '/dashboard/') -> bool:
    """Envía push notification via Firebase FCM."""
    if not usuario.fcm_token or not settings.FIREBASE_CREDENTIALS_PATH:
        logger.info(f'[DEBUG PUSH] Para {usuario.nombre}: {titulo} - {cuerpo}')
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)

        message = messaging.Message(
            notification=messaging.Notification(title=titulo, body=cuerpo),
            data={'url': url},
            token=usuario.fcm_token,
        )
        messaging.send(message)
        return True
    except Exception as e:
        logger.error(f'Error push a {usuario.nombre}: {e}')
        return False


def crear_notificacion_interna(usuario, titulo, mensaje, tipo='recordatorio', url=''):
    """Crea notificación interna en base de datos."""
    from apps.notificaciones.models import Notificacion
    return Notificacion.objects.create(
        usuario=usuario,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        url_accion=url,
    )
