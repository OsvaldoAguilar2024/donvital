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
            name='Paciente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=150, verbose_name='Nombre completo')),
                ('fecha_nacimiento', models.DateField(blank=True, null=True)),
                ('telefono', models.CharField(blank=True, max_length=20)),
                ('eps', models.CharField(blank=True, max_length=100, verbose_name='EPS')),
                ('numero_afiliacion', models.CharField(blank=True, max_length=50)),
                ('grupo_sanguineo', models.CharField(blank=True, max_length=10)),
                ('alergias', models.TextField(blank=True)),
                ('condiciones', models.TextField(blank=True)),
                ('medicamentos_actuales', models.TextField(blank=True)),
                ('contacto_emergencia', models.CharField(blank=True, max_length=150)),
                ('telefono_emergencia', models.CharField(blank=True, max_length=20)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='pacientes/fotos/')),
                ('foto_carnet_eps', models.ImageField(blank=True, null=True, upload_to='pacientes/carnets/')),
                ('activo', models.BooleanField(default=True)),
                ('notas', models.TextField(blank=True)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('actualizado_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Paciente', 'verbose_name_plural': 'Pacientes', 'ordering': ['nombre']},
        ),
        migrations.CreateModel(
            name='CuidadorPaciente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.CharField(choices=[('principal','Cuidador Principal'),('extra','Cuidador Adicional')], default='principal', max_length=15)),
                ('activo', models.BooleanField(default=True)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cuidadores_pacientes', to=settings.AUTH_USER_MODEL)),
                ('paciente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cuidadores', to='pacientes.paciente')),
            ],
            options={'verbose_name': 'Cuidador - Paciente'},
        ),
        migrations.AlterUniqueTogether(
            name='cuidadorpaciente',
            unique_together={('usuario', 'paciente')},
        ),
    ]
