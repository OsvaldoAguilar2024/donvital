#!/bin/bash
echo "=== DON VITAL - Setup Local ==="
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations usuarios pacientes citas notificaciones suscripciones medicamentos
python manage.py migrate
python manage.py loaddata fixtures/datos_iniciales.json
python manage.py shell -c "
from apps.usuarios.models import Usuario
if not Usuario.objects.filter(telefono='+573001234567').exists():
    Usuario.objects.create_superuser(telefono='+573001234567', nombre='Admin Don Vital', password='admin123')
    print('✅ Superuser creado: +573001234567 / admin123')
"
echo "=== Listo. Abre http://localhost:8000 ==="
python manage.py runserver
