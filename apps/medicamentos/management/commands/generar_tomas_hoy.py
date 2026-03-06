"""
Comando para generar registros de toma del día y disparar recordatorios.
Uso: python manage.py generar_tomas_hoy
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Genera registros de toma del día y dispara recordatorios pendientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--solo-generar',
            action='store_true',
            help='Solo genera registros sin disparar recordatorios',
        )
        parser.add_argument(
            '--solo-enviar',
            action='store_true',
            help='Solo dispara recordatorios sin generar registros',
        )

    def handle(self, *args, **options):
        from apps.medicamentos.tasks import (
            generar_registros_toma_diarios,
            verificar_y_enviar_tomas,
        )

        solo_generar = options['solo_generar']
        solo_enviar = options['solo_enviar']
        hoy = timezone.now().date()

        self.stdout.write(f'\n🗓️  Don Vital — {hoy}\n')

        if not solo_enviar:
            self.stdout.write('⚙️  Generando registros de toma...')
            resultado = generar_registros_toma_diarios()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Registros creados: {resultado["creados"]}')
            )

        if not solo_generar:
            self.stdout.write('📱 Disparando recordatorios en ventana actual...')
            resultado = verificar_y_enviar_tomas()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Recordatorios enviados: {resultado["enviados"]}')
            )

        self.stdout.write(self.style.SUCCESS('\n✅ Listo.\n'))
