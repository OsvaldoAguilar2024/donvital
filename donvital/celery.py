import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'donvital.settings')

app = Celery('donvital')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'verificar-y-enviar-recordatorios': {
        'task': 'apps.notificaciones.tasks.verificar_y_enviar_recordatorios',
        'schedule': crontab(minute=0),  # cada hora en punto
    },
    'verificar-citas-sin-confirmar': {
        'task': 'apps.notificaciones.tasks.verificar_citas_sin_confirmar',
        'schedule': crontab(minute=30),  # cada hora a los 30 minutos
    },
    'generar-tomas-diarias': {
        'task': 'apps.medicamentos.tasks.generar_registros_toma_diarios',
        'schedule': crontab(hour=0, minute=5),
    },
    'verificar-stock-recetas': {
        'task': 'apps.medicamentos.tasks.verificar_stock_y_recetas',
        'schedule': crontab(hour=8, minute=0),
    },
    'verificar-y-enviar-tomas': {
    'task': 'apps.medicamentos.tasks.verificar_y_enviar_tomas',
    'schedule': crontab(minute=0),
    },
}
