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
            name='Medicamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200)),
                ('principio_activo', models.CharField(blank=True, max_length=200)),
                ('presentacion', models.CharField(blank=True, max_length=100)),
                ('dosis', models.CharField(max_length=100)),
                ('via_administracion', models.CharField(blank=True, max_length=80)),
                ('instrucciones', models.TextField(blank=True)),
                ('frecuencia_tipo', models.CharField(choices=[('cada_horas','Cada X horas'),('veces_dia','X veces al día'),('dias_esp','Días específicos'),('necesidad','Solo cuando se necesite')], default='veces_dia', max_length=15)),
                ('intervalo_horas', models.PositiveIntegerField(blank=True, null=True)),
                ('horarios_fijos', models.JSONField(blank=True, default=list)),
                ('dias_semana', models.JSONField(blank=True, default=list)),
                ('medico_prescriptor', models.CharField(blank=True, max_length=150)),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField(blank=True, null=True)),
                ('duracion_dias', models.PositiveIntegerField(blank=True, null=True)),
                ('numero_receta', models.CharField(blank=True, max_length=100)),
                ('foto_receta', models.ImageField(blank=True, null=True, upload_to='medicamentos/recetas/')),
                ('stock_actual', models.PositiveIntegerField(blank=True, null=True)),
                ('stock_minimo_alerta', models.PositiveIntegerField(blank=True, null=True)),
                ('fecha_vencimiento_medicamento', models.DateField(blank=True, null=True)),
                ('requiere_renovacion_receta', models.BooleanField(default=False)),
                ('fecha_vencimiento_receta', models.DateField(blank=True, null=True)),
                ('dias_alerta_vencimiento_receta', models.PositiveIntegerField(default=7)),
                ('estado', models.CharField(choices=[('activo','Activo'),('pausado','Pausado'),('suspendido','Suspendido')], default='activo', max_length=15)),
                ('notas', models.TextField(blank=True)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('actualizado_at', models.DateTimeField(auto_now=True)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medicamentos', to='pacientes.paciente')),
                ('registrado_por', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='medicamentos_registrados', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Medicamento', 'verbose_name_plural': 'Medicamentos', 'ordering': ['paciente', 'nombre']},
        ),
        migrations.CreateModel(
            name='RegistroToma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_programada', models.DateField()),
                ('hora_programada', models.TimeField()),
                ('estado', models.CharField(choices=[('pendiente','⏳ Pendiente'),('tomado','✅ Tomado'),('omitido','❌ Omitido'),('retrasado','⚠️ Retrasado')], default='pendiente', max_length=10)),
                ('hora_real_toma', models.DateTimeField(blank=True, null=True)),
                ('notas_toma', models.CharField(blank=True, max_length=200)),
                ('unidades_consumidas', models.PositiveIntegerField(default=1)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('medicamento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registros_toma', to='medicamentos.medicamento')),
                ('confirmado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tomas_confirmadas', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Registro de Toma', 'ordering': ['-fecha_programada', '-hora_programada']},
        ),
        migrations.AlterUniqueTogether(
            name='registrotoma',
            unique_together={('medicamento', 'fecha_programada', 'hora_programada')},
        ),
        migrations.CreateModel(
            name='HistorialMedicamento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(max_length=100)),
                ('detalle', models.TextField(blank=True)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('medicamento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historial', to='medicamentos.medicamento')),
                ('usuario', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Historial Medicamento', 'ordering': ['-creado_at']},
        ),
    ]
