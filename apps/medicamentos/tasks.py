"""
DON VITAL - Tareas Celery para recordatorios de medicamentos
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task
def generar_registros_toma_diarios():
    """
    Tarea diaria (00:05 AM) que genera los RegistroToma del día
    para todos los medicamentos activos.
    """
    from .models import Medicamento, RegistroToma
    from datetime import time, timedelta

    hoy = timezone.now().date()
    dia_semana = hoy.weekday()  # 0=Lunes, 6=Domingo
    creados = 0

    medicamentos = Medicamento.objects.filter(
        estado=Medicamento.ESTADO_ACTIVO
    ).select_related('paciente')

    for med in medicamentos:
        # Verificar si el medicamento ya empezó y no ha terminado
        if med.fecha_inicio > hoy:
            continue
        if med.fecha_fin and med.fecha_fin < hoy:
            med.estado = Medicamento.ESTADO_SUSPENDIDO
            med.save(update_fields=['estado'])
            continue

        horarios = []

        if med.frecuencia_tipo == Medicamento.FREQ_VECES_DIA:
            horarios = med.horarios_fijos or []

        elif med.frecuencia_tipo == Medicamento.FREQ_CADA_HORAS and med.intervalo_horas:
            # Generar horarios a lo largo del día
            hora_actual = time(0, 0)
            inicio_dt = timezone.make_aware(
                timezone.datetime.combine(med.fecha_inicio, time(8, 0))
            )
            ahora = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            horas_desde_inicio = int((ahora - inicio_dt).total_seconds() // 3600)
            offset = horas_desde_inicio % med.intervalo_horas

            h = (8 + (med.intervalo_horas - offset) % med.intervalo_horas) % 24
            while h < 24:
                horarios.append(f'{h:02d}:00')
                h += med.intervalo_horas

        elif med.frecuencia_tipo == Medicamento.FREQ_DIAS_ESPECIFICOS:
            if dia_semana not in (med.dias_semana or []):
                continue
            horarios = med.horarios_fijos or ['08:00']

        elif med.frecuencia_tipo == Medicamento.FREQ_SEGUN_NECESIDAD:
            continue  # No genera registros automáticos

        for horario_str in horarios:
            try:
                hora, minuto = horario_str.split(':')
                hora_toma = time(int(hora), int(minuto))
                obj, created = RegistroToma.objects.get_or_create(
                    medicamento=med,
                    fecha_programada=hoy,
                    hora_programada=hora_toma,
                    defaults={'estado': RegistroToma.ESTADO_PENDIENTE}
                )
                if created:
                    creados += 1
            except (ValueError, Exception) as e:
                logger.error(f'Error creando registro toma para {med}: {e}')

    logger.info(f'Registros de toma generados: {creados} para {hoy}')
    return {'creados': creados, 'fecha': str(hoy)}


@shared_task
def enviar_recordatorio_medicamento(registro_toma_id: int):
    """Envía recordatorio de toma de medicamento."""
    from .models import RegistroToma
    from apps.pacientes.models import CuidadorPaciente
    from apps.notificaciones.services import enviar_push, enviar_sms, crear_notificacion_interna

    try:
        registro = RegistroToma.objects.select_related(
            'medicamento__paciente'
        ).get(id=registro_toma_id)

        if registro.estado != RegistroToma.ESTADO_PENDIENTE:
            return {'status': 'ya_procesado'}

        med = registro.medicamento
        paciente = med.paciente
        hora_str = registro.hora_programada.strftime('%H:%M')

        titulo = f'💊 Medicamento: {med.nombre}'
        mensaje = (
            f'Es hora de que {paciente.nombre} tome {med.dosis} de {med.nombre}. '
            f'Hora programada: {hora_str}.'
        )
        if med.instrucciones:
            mensaje += f' Recordar: {med.instrucciones[:80]}'

        url = f'/medicamentos/toma/{registro.id}/confirmar/'

        # Notificar a todos los cuidadores
        cuidadores = CuidadorPaciente.objects.filter(
            paciente=paciente, activo=True
        ).select_related('usuario')

        for rel in cuidadores:
            usuario = rel.usuario
            crear_notificacion_interna(
                usuario=usuario, titulo=titulo,
                mensaje=mensaje, tipo='recordatorio', url=url
            )
            if usuario.notif_push:
                enviar_push(usuario, titulo, mensaje, url)

        # Marcar como retrasado si ya pasó más de 30 min
        registro.estado = RegistroToma.ESTADO_RETRASADO
        registro.save(update_fields=['estado'])

        return {'status': 'enviado', 'medicamento': med.nombre}

    except RegistroToma.DoesNotExist:
        return {'status': 'no_encontrado'}
    except Exception as e:
        logger.error(f'Error enviando recordatorio medicamento {registro_toma_id}: {e}')
        return {'status': 'error', 'error': str(e)}


@shared_task
def verificar_stock_y_recetas():
    """
    Tarea diaria: alerta sobre stock bajo y recetas por vencer.
    """
    from .models import Medicamento
    from apps.pacientes.models import CuidadorPaciente
    from apps.notificaciones.services import crear_notificacion_interna, enviar_push

    hoy = timezone.now().date()
    medicamentos = Medicamento.objects.filter(
        estado=Medicamento.ESTADO_ACTIVO
    ).select_related('paciente')

    for med in medicamentos:
        cuidadores = CuidadorPaciente.objects.filter(
            paciente=med.paciente, activo=True
        ).select_related('usuario')

        # Alerta stock bajo
        if med.stock_bajo:
            titulo = f'⚠️ Stock bajo: {med.nombre}'
            mensaje = (
                f'{med.paciente.nombre} tiene solo {med.stock_actual} unidades '
                f'de {med.nombre}. Mínimo recomendado: {med.stock_minimo_alerta}.'
            )
            for rel in cuidadores:
                crear_notificacion_interna(
                    rel.usuario, titulo, mensaje, tipo='alerta',
                    url=f'/medicamentos/{med.id}/'
                )

        # Alerta medicamento vencido
        if med.medicamento_vencido:
            titulo = f'❌ Medicamento vencido: {med.nombre}'
            mensaje = f'{med.nombre} de {med.paciente.nombre} venció el {med.fecha_vencimiento_medicamento}. No administrar.'
            for rel in cuidadores:
                crear_notificacion_interna(rel.usuario, titulo, mensaje, tipo='alerta')

        # Alerta receta por vencer
        if med.requiere_renovacion_receta and med.receta_vence_pronto:
            dias = (med.fecha_vencimiento_receta - hoy).days
            titulo = f'📋 Receta por vencer: {med.nombre}'
            mensaje = (
                f'La receta de {med.nombre} para {med.paciente.nombre} '
                f'vence en {dias} día{"s" if dias != 1 else ""}. '
                f'Solicitar renovación al médico.'
            )
            for rel in cuidadores:
                crear_notificacion_interna(rel.usuario, titulo, mensaje, tipo='alerta')

        # Alerta receta ya vencida
        if med.requiere_renovacion_receta and med.receta_vencida:
            titulo = f'❌ Receta vencida: {med.nombre}'
            mensaje = f'La receta de {med.nombre} para {med.paciente.nombre} está vencida. Renovar urgente.'
            for rel in cuidadores:
                crear_notificacion_interna(rel.usuario, titulo, mensaje, tipo='alerta')

    return {'status': 'ok', 'fecha': str(hoy)}


@shared_task
def programar_recordatorios_medicamentos_hoy():
    """
    Programa las tareas Celery de recordatorio para cada toma del día.
    Se ejecuta después de generar_registros_toma_diarios.
    """
    from .models import RegistroToma
    from datetime import datetime

    hoy = timezone.now().date()
    registros = RegistroToma.objects.filter(
        fecha_programada=hoy,
        estado=RegistroToma.ESTADO_PENDIENTE,
        medicamento__estado=Medicamento.ESTADO_ACTIVO,
    )

    programados = 0
    for registro in registros:
        hora = registro.hora_programada
        momento = timezone.make_aware(datetime.combine(hoy, hora))

        if momento > timezone.now():
            enviar_recordatorio_medicamento.apply_async(
                args=[registro.id],
                eta=momento
            )
            programados += 1

    return {'programados': programados}
