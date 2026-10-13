"""
Corre todo lo programado sin Celery ni Redis: pensado para un cron de Railway.
Uso: python manage.py enviar_recordatorios
Es seguro correrlo varias veces: no duplica tomas ni recordatorios ya enviados.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Genera las tomas del día y envía recordatorios de tomas y citas'

    def handle(self, *args, **options):
        from apps.medicamentos.tasks import generar_registros_toma_diarios, verificar_y_enviar_tomas
        from apps.notificaciones.tasks import verificar_y_enviar_recordatorios

        ahora = timezone.localtime()
        self.stdout.write(f'Don Vital · {ahora:%Y-%m-%d %H:%M} (hora Colombia)')
        r1 = generar_registros_toma_diarios()
        r2 = verificar_y_enviar_tomas()
        r3 = verificar_y_enviar_recordatorios()
        self.stdout.write(self.style.SUCCESS(
            f"Tomas creadas: {r1['creados']} · recordatorios de tomas: {r2['enviados']} · "
            f"recordatorios de citas: {r3.get('enviados', 0)}"
        ))
