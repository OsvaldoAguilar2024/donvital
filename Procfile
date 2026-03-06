web: gunicorn donvital.wsgi --bind 0.0.0.0:$PORT --workers 2
worker: celery -A donvital worker --loglevel=info
beat: celery -A donvital beat --loglevel=info

