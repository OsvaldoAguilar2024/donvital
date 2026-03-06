"""
Comando para programar recordatorios de citas pendientes y disparar los que están en ventana.
Uso: python manage.py verificar_recordatorios_citas
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Programa recordatorios de citas sin recordatorios y dispara los que están en ventana'

    def add_arguments(self, parser):
        parser.add_argument(
            '--solo-programar',
            action='store_true',
            help='Solo programa recordatorios faltantes sin disparar envíos',
        )
        parser.add_argument(
            '--solo-enviar',
            action='store_true',
            help='Solo dispara recordatorios en ventana sin programar nuevos',
        )

    def handle(self, *args, **options):
        from apps.notificaciones.tasks import (
            programar_recordatorios_cita,
            verificar_y_enviar_recordatorios,
        )
        from apps.citas.models import Cita, Recordatorio

        solo_programar = options['solo_programar']
        solo_enviar = options['solo_enviar']

        self.stdout.write(f'\n🗓️  Don Vital — {timezone.now().date()}\n')

        if not solo_enviar:
            # Buscar citas futuras sin recordatorios
            citas_sin_recordatorios = Cita.objects.filter(
                fecha__gte=timezone.now().date(),
                estado__in=['programada', 'confirmada'],
            ).exclude(
                id__in=Recordatorio.objects.values_list('cita_id', flat=True)
            )

            self.stdout.write(f'⚙️  Citas sin recordatorios: {citas_sin_recordatorios.count()}')
            programadas = 0
            for cita in citas_sin_recordatorios:
                resultado = programar_recordatorios_cita(cita.id)
                programadas += resultado.get('recordatorios_creados', 0)

            self.stdout.write(
                self.style.SUCCESS(f'✅ Recordatorios programados: {programadas}')
            )

        if not solo_programar:
            self.stdout.write('📱 Disparando recordatorios en ventana actual...')
            resultado = verificar_y_enviar_recordatorios()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Recordatorios enviados: {resultado.get("enviados", 0)}')
            )

        self.stdout.write(self.style.SUCCESS('\n✅ Listo.\n'))
