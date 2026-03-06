"""
DON VITAL - Tareas Celery para notificaciones asíncronas
"""
from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def programar_recordatorios_cita(cita_id: int):
    """
    Crea los registros Recordatorio para una cita nueva.
    Se llama desde views.py al crear una cita.
    """
    from apps.citas.models import Cita, Recordatorio

    try:
        cita = Cita.objects.select_related('paciente', 'especialidad').get(id=cita_id)
        fecha_hora = timezone.make_aware(datetime.combine(cita.fecha, cita.hora))
        ahora = timezone.now()

        tipos_config = [
            ('72h', fecha_hora - timedelta(hours=72)),
            ('24h', fecha_hora - timedelta(hours=24)),
            ('2h',  fecha_hora - timedelta(hours=2)),
            ('post', fecha_hora + timedelta(hours=2)),
        ]

        creados = 0
        for tipo, momento in tipos_config:
            if momento <= ahora:
                continue
            for canal in ['push', 'sms']:
                _, created = Recordatorio.objects.get_or_create(
                    cita=cita,
                    tipo=tipo,
                    canal=canal,
                )
                if created:
                    creados += 1

        logger.info(f'Recordatorios creados para cita {cita_id}: {creados}')
        return {'status': 'ok', 'cita': cita_id, 'recordatorios_creados': creados}

    except Exception as e:
        logger.error(f'Error programando recordatorios cita {cita_id}: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task
def verificar_y_enviar_recordatorios():
    """
    Tarea periódica que corre cada hora.
    Busca recordatorios pendientes y los envía.
    """
    from apps.citas.models import Cita, Recordatorio
    from apps.pacientes.models import CuidadorPaciente
    from .services import enviar_push, enviar_sms, crear_notificacion_interna

    ahora = timezone.now()
    ventana_inicio = ahora - timedelta(minutes=30)
    ventana_fin = ahora + timedelta(minutes=30)

    # Buscar citas con recordatorios pendientes en la ventana de ±30 min
    citas = Cita.objects.filter(
        estado__in=['programada', 'confirmada'],
    ).select_related('paciente', 'especialidad')

    enviados = 0

    for cita in citas:
        fecha_hora = timezone.make_aware(datetime.combine(cita.fecha, cita.hora))

        # Calcular momentos de cada tipo
        momentos = {
            '72h': fecha_hora - timedelta(hours=72),
            '24h': fecha_hora - timedelta(hours=24),
            '2h':  fecha_hora - timedelta(hours=2),
            'post': fecha_hora + timedelta(hours=2),
        }

        # Obtener cuidadores del paciente
        cuidadores = list(
            CuidadorPaciente.objects.filter(
                paciente=cita.paciente, activo=True
            ).select_related('usuario').values_list('usuario', flat=True)
        )

        if not cuidadores:
            continue

        from apps.usuarios.models import Usuario
        usuarios = Usuario.objects.filter(id__in=cuidadores)

        for tipo, momento in momentos.items():
            # ¿Está este momento en la ventana de envío?
            if not (ventana_inicio <= momento <= ventana_fin):
                continue

            # Buscar o crear el recordatorio
            recordatorio_push, _ = Recordatorio.objects.get_or_create(
                cita=cita, tipo=tipo, canal='push'
            )
            recordatorio_sms, _ = Recordatorio.objects.get_or_create(
                cita=cita, tipo=tipo, canal='sms'
            )

            if recordatorio_push.enviado and recordatorio_sms.enviado:
                continue

            # Construir mensaje
            paciente = cita.paciente
            esp = str(cita.especialidad) if cita.especialidad else 'médica'
            mensajes = {
                '72h': {
                    'titulo': f'📅 Cita de {paciente.nombre} en 3 días',
                    'cuerpo': f'El {cita.fecha.strftime("%d/%m")} a las {cita.hora.strftime("%H:%M")} con {esp} en {cita.lugar or "consulta"}.',
                },
                '24h': {
                    'titulo': f'🔔 Cita de {paciente.nombre} mañana',
                    'cuerpo': f'Mañana a las {cita.hora.strftime("%H:%M")} - {esp}. Documentos: {cita.documentos_requeridos or "carnet EPS"}.',
                },
                '2h': {
                    'titulo': f'⏰ En 2 horas: Cita de {paciente.nombre}',
                    'cuerpo': f'La cita es a las {cita.hora.strftime("%H:%M")} en {cita.lugar or "consulta"}. ¡Es hora de prepararse!',
                },
                'post': {
                    'titulo': f'✅ ¿Cómo fue la cita de {paciente.nombre}?',
                    'cuerpo': '¿Hubo cambios en el tratamiento o nuevas indicaciones médicas?',
                },
            }
            msg = mensajes[tipo]
            url_cita = f'/citas/{cita.id}/'

            for usuario in usuarios:
                # Notificación interna siempre
                try:
                    crear_notificacion_interna(
                        usuario=usuario,
                        titulo=msg['titulo'],
                        mensaje=msg['cuerpo'],
                        cita=cita,
                        tipo='recordatorio',
                        url=url_cita
                    )
                except Exception as e:
                    logger.error(f'Error notif interna: {e}')

                # Push
                if not recordatorio_push.enviado:
                    try:
                        enviar_push(usuario, msg['titulo'], msg['cuerpo'], url_cita)
                    except Exception as e:
                        logger.error(f'Error push: {e}')

                # SMS
                if not recordatorio_sms.enviado:
                    try:
                        sms_text = f"Don Vital: {msg['titulo']} - {msg['cuerpo']}"
                        enviar_sms(usuario.telefono, sms_text[:160])
                    except Exception as e:
                        logger.error(f'Error SMS: {e}')

            # Marcar como enviados
            if not recordatorio_push.enviado:
                recordatorio_push.enviado = True
                recordatorio_push.enviado_at = ahora
                recordatorio_push.save()
                enviados += 1

            if not recordatorio_sms.enviado:
                recordatorio_sms.enviado = True
                recordatorio_sms.enviado_at = ahora
                recordatorio_sms.save()
                enviados += 1

    logger.info(f'Recordatorios enviados: {enviados}')
    return {'status': 'ok', 'enviados': enviados}


@shared_task
def verificar_citas_sin_confirmar():
    """
    Tarea periódica: detecta citas en las próximas 4 horas sin confirmar.
    """
    from apps.citas.models import Cita
    from apps.pacientes.models import CuidadorPaciente
    from .services import enviar_push, crear_notificacion_interna

    ahora = timezone.now()
    limite = ahora + timedelta(hours=4)

    citas = Cita.objects.filter(
        estado=Cita.ESTADO_PROGRAMADA,
        fecha__gte=ahora.date(),
    ).select_related('paciente', 'especialidad')

    for cita in citas:
        cita_fecha_hora = timezone.make_aware(datetime.combine(cita.fecha, cita.hora))
        if not (ahora < cita_fecha_hora < limite):
            continue

        cuidadores = CuidadorPaciente.objects.filter(
            paciente=cita.paciente, activo=True
        ).select_related('usuario')

        for rel in cuidadores:
            usuario = rel.usuario
            titulo = '⚠️ Cita sin confirmar'
            mensaje = (
                f'{cita.paciente.nombre} tiene cita con {cita.especialidad} '
                f'en menos de 4h. ¡Aún no está confirmada!'
            )
            try:
                crear_notificacion_interna(usuario, titulo, mensaje, cita, 'alerta')
                if usuario.notif_push:
                    enviar_push(usuario, titulo, mensaje, f'/citas/{cita.id}/')
            except Exception as e:
                logger.error(f'Error alerta sin confirmar: {e}')