from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pacientes', '0001_initial'),
    ]
    operations = [
        migrations.CreateModel(
            name='Especialidad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('icono', models.CharField(default='🏥', max_length=10)),
                ('activa', models.BooleanField(default=True)),
            ],
            options={'verbose_name': 'Especialidad', 'verbose_name_plural': 'Especialidades', 'ordering': ['nombre']},
        ),
        migrations.CreateModel(
            name='Cita',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medico', models.CharField(blank=True, max_length=150)),
                ('fecha', models.DateField()),
                ('hora', models.TimeField()),
                ('lugar', models.CharField(blank=True, max_length=200)),
                ('direccion', models.CharField(blank=True, max_length=250)),
                ('estado', models.CharField(choices=[('programada','Programada'),('confirmada','Confirmada'),('completada','Completada'),('cancelada','Cancelada'),('perdida','Perdida')], default='programada', max_length=15)),
                ('documentos_requeridos', models.TextField(blank=True)),
                ('notas', models.TextField(blank=True)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('actualizado_at', models.DateTimeField(auto_now=True)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='citas', to='pacientes.paciente')),
                ('especialidad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='citas.especialidad')),
                ('creado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='citas_creadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Cita', 'verbose_name_plural': 'Citas', 'ordering': ['fecha', 'hora']},
        ),
        migrations.CreateModel(
            name='Recordatorio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('72h','72 horas antes'),('24h','24 horas antes'),('2h','2 horas antes'),('post','Post cita')], max_length=5)),
                ('canal', models.CharField(choices=[('push','Push'),('sms','SMS'),('whatsapp','WhatsApp')], default='push', max_length=10)),
                ('enviado', models.BooleanField(default=False)),
                ('enviado_at', models.DateTimeField(blank=True, null=True)),
                ('error', models.TextField(blank=True)),
                ('cita', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recordatorios', to='citas.cita')),
            ],
            options={'verbose_name': 'Recordatorio'},
        ),
        migrations.AlterUniqueTogether(
            name='recordatorio',
            unique_together={('cita', 'tipo', 'canal')},
        ),
    ]
