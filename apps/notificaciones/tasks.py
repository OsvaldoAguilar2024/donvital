"""
DON VITAL - Tareas Celery para notificaciones asíncronas
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def enviar_recordatorio_cita(self, recordatorio_id: int):
    """Envía un recordatorio de cita (push + SMS según configuración del usuario)."""
    try:
        from apps.citas.models import Recordatorio
        from .services import enviar_push, enviar_sms, crear_notificacion_interna
        
        recordatorio = Recordatorio.objects.select_related(
            'cita__paciente', 'cita__especialidad', 'usuario'
        ).get(id=recordatorio_id)
        
        if recordatorio.enviado:
            return {'status': 'ya_enviado'}
        
        cita = recordatorio.cita
        usuario = recordatorio.usuario
        paciente = cita.paciente
        
        # Construir mensaje según tipo
        mensajes = {
            '72h': {
                'titulo': f'📅 Cita de {paciente.nombre} en 3 días',
                'cuerpo': f'El {cita.fecha.strftime("%d/%m")} a las {cita.hora.strftime("%H:%M")} con {cita.especialidad} en {cita.lugar}. ¿Confirmar asistencia?',
            },
            '24h': {
                'titulo': f'🔔 Cita de {paciente.nombre} mañana',
                'cuerpo': f'Mañana a las {cita.hora.strftime("%H:%M")} tienes cita con {cita.especialidad}. Documentos: {cita.documentos_requeridos or "carnet EPS"}',
            },
            '2h': {
                'titulo': f'⏰ En 2 horas: Cita de {paciente.nombre}',
                'cuerpo': f'La cita es a las {cita.hora.strftime("%H:%M")} en {cita.lugar}. ¡Es hora de prepararse!',
            },
            'post': {
                'titulo': f'✅ ¿Cómo fue la cita de {paciente.nombre}?',
                'cuerpo': '¿Hubo cambios en el tratamiento o nuevas indicaciones médicas?',
            },
        }
        
        msg = mensajes.get(recordatorio.tipo, {
            'titulo': f'Recordatorio: {paciente.nombre}',
            'cuerpo': f'Cita con {cita.especialidad} el {cita.fecha}'
        })
        
        url_cita = f'/citas/{cita.id}/'
        exito = False
        
        # Enviar según canal configurado
        if recordatorio.canal == 'push' and usuario.notif_push:
            exito = enviar_push(usuario, msg['titulo'], msg['cuerpo'], url_cita)
        elif recordatorio.canal == 'sms' and usuario.notif_sms:
            sms_text = f"Don Vital: {msg['titulo']}\n{msg['cuerpo']}"
            exito = enviar_sms(usuario.telefono, sms_text[:160])
        
        # Siempre crear notificación interna
        crear_notificacion_interna(
            usuario=usuario, titulo=msg['titulo'],
            mensaje=msg['cuerpo'], cita=cita,
            tipo='recordatorio', url=url_cita
        )
        
        recordatorio.enviado = True
        recordatorio.enviado_at = timezone.now()
        if not exito:
            recordatorio.error = 'Canal no disponible o falló envío'
        recordatorio.save()
        
        return {'status': 'enviado', 'canal': recordatorio.canal}
        
    except Exception as exc:
        logger.error(f'Error enviando recordatorio {recordatorio_id}: {exc}')
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task
def programar_recordatorios_cita(cita_id: int):
    """Programa todos los recordatorios para una cita nueva."""
    from apps.citas.models import Cita, Recordatorio
    from apps.pacientes.models import CuidadorPaciente
    from datetime import timedelta
    
    try:
        cita = Cita.objects.select_related('paciente', 'especialidad').get(id=cita_id)
        fecha_hora = cita.fecha_hora
        
        # Obtener todos los cuidadores del paciente
        relaciones = CuidadorPaciente.objects.filter(
            paciente=cita.paciente, activo=True
        ).select_related('usuario')
        
        cuidadores = [rel.usuario for rel in relaciones]
        
        recordatorios_config = [
            ('72h', fecha_hora - timedelta(hours=72), ['push', 'sms']),
            ('24h', fecha_hora - timedelta(hours=24), ['push', 'sms']),
            ('2h', fecha_hora - timedelta(hours=2), ['push', 'sms']),
            ('post', fecha_hora + timedelta(hours=2), ['push']),
        ]
        
        ahora = timezone.now()
        
        for tipo, momento, canales in recordatorios_config:
            if momento <= ahora:
                continue
            
            for usuario in cuidadores:
                for canal in canales:
                    # Evitar duplicados
                    if not Recordatorio.objects.filter(
                        cita=cita, usuario=usuario, tipo=tipo, canal=canal
                    ).exists():
                        recordatorio = Recordatorio.objects.create(
                            cita=cita, usuario=usuario,
                            tipo=tipo, canal=canal,
                            programado_para=momento
                        )
                        # Programar la tarea Celery
                        enviar_recordatorio_cita.apply_async(
                            args=[recordatorio.id],
                            eta=momento
                        )
        
        logger.info(f'Recordatorios programados para cita {cita_id}')
        return {'status': 'ok', 'cita': cita_id}
    
    except Exception as e:
        logger.error(f'Error programando recordatorios cita {cita_id}: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task
def verificar_citas_sin_confirmar():
    """
    Tarea periódica: detecta citas próximas sin confirmar y alerta a todos los cuidadores.
    Se ejecuta cada hora via Celery Beat.
    """
    from apps.citas.models import Cita
    from .services import enviar_push, enviar_sms, crear_notificacion_interna
    from apps.pacientes.models import CuidadorPaciente
    from datetime import timedelta
    
    ahora = timezone.now()
    limite = ahora + timedelta(hours=4)
    
    citas_sin_confirmar = Cita.objects.filter(
        estado=Cita.ESTADO_PROGRAMADA,
        fecha__gte=ahora.date(),
    ).select_related('paciente', 'especialidad')
    
    for cita in citas_sin_confirmar:
        if ahora < cita.fecha_hora < limite:
            cuidadores = CuidadorPaciente.objects.filter(
                paciente=cita.paciente, activo=True
            ).select_related('usuario')
            
            for rel in cuidadores:
                usuario = rel.usuario
                titulo = f'⚠️ ATENCIÓN: Cita sin confirmar'
                mensaje = (
                    f'{cita.paciente.nombre} tiene cita con {cita.especialidad} '
                    f'en {cita.horas_restantes:.0f}h. ¡Aún no está confirmada!'
                )
                crear_notificacion_interna(usuario, titulo, mensaje, cita, 'alerta')
                if usuario.notif_push:
                    enviar_push(usuario, titulo, mensaje, f'/citas/{cita.id}/')
