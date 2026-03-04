@echo off
echo === DON VITAL - Setup Local ===
echo.

python -m venv venv
call venv\Scripts\activate

pip install -r requirements.txt

python manage.py makemigrations usuarios pacientes citas notificaciones suscripciones medicamentos
python manage.py migrate

python manage.py loaddata fixtures/datos_iniciales.json

python manage.py shell -c "from apps.usuarios.models import Usuario; Usuario.objects.filter(telefono='+573001234567').exists() or Usuario.objects.create_superuser(telefono='+573001234567', nombre='Admin Don Vital', password='admin123')"

echo.
echo === Setup completo ===
echo Abre http://localhost:8000
echo Admin: +573001234567 / admin123
echo.
python manage.py runserver
