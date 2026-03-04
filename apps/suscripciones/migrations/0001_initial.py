from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('precio_usd', models.DecimalField(decimal_places=2, max_digits=8)),
                ('precio_cop', models.IntegerField()),
                ('max_pacientes', models.PositiveIntegerField(default=2)),
                ('max_cuidadores', models.PositiveIntegerField(default=1)),
                ('descripcion', models.TextField(blank=True)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={'verbose_name': 'Plan'},
        ),
        migrations.CreateModel(
            name='Suscripcion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[('trial','Período gratuito'),('activa','Activa'),('vencida','Vencida'),('cancelada','Cancelada')], default='trial', max_length=15)),
                ('meses_gratis', models.PositiveIntegerField(default=0)),
                ('fecha_inicio', models.DateField(default=django.utils.timezone.now)),
                ('fecha_fin', models.DateField(blank=True, null=True)),
                ('codigo_referido', models.CharField(blank=True, max_length=20)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='suscripciones', to=settings.AUTH_USER_MODEL)),
                ('plan', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='suscripciones.plan')),
            ],
            options={'verbose_name': 'Suscripción'},
        ),
    ]
