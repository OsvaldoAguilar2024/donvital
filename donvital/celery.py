import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donvital.settings')

app = Celery('donvital')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'verificar-recordatorios-cada-hora': {
        'task': 'apps.notificaciones.tasks.verificar_citas_sin_confirmar',
        'schedule': crontab(minute=0),  # cada hora en punto
    },
    'generar-tomas-diarias': {
        'task': 'apps.medicamentos.tasks.generar_registros_toma_diarios',
        'schedule': crontab(hour=0, minute=5),  # cada día a las 00:05
    },
    'verificar-stock-recetas': {
        'task': 'apps.medicamentos.tasks.verificar_stock_y_recetas',
        'schedule': crontab(hour=8, minute=0),  # cada día a las 8am
    },
}
