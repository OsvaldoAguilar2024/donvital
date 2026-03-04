from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='Notificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('recordatorio','Recordatorio'),('alerta','Alerta'),('info','Información')], default='info', max_length=15)),
                ('titulo', models.CharField(max_length=200)),
                ('mensaje', models.TextField()),
                ('leida', models.BooleanField(default=False)),
                ('leida_at', models.DateTimeField(blank=True, null=True)),
                ('url_accion', models.CharField(blank=True, max_length=200)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notificaciones', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Notificación', 'verbose_name_plural': 'Notificaciones', 'ordering': ['-creado_at']},
        ),
        migrations.CreateModel(
            name='LogAuditoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(max_length=100)),
                ('tabla_afectada', models.CharField(blank=True, max_length=50)),
                ('objeto_id', models.IntegerField(blank=True, null=True)),
                ('detalles', models.JSONField(blank=True, default=dict)),
                ('ip', models.GenericIPAddressField(blank=True, null=True)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Log de Auditoría', 'ordering': ['-creado_at']},
        ),
    ]
