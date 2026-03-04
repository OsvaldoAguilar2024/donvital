from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]
    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False)),
                ('telefono', models.CharField(max_length=20, unique=True, verbose_name='Teléfono')),
                ('nombre', models.CharField(max_length=150, verbose_name='Nombre completo')),
                ('email', models.EmailField(blank=True, verbose_name='Correo electrónico')),
                ('rol', models.CharField(choices=[('paciente','Paciente'),('cuidador_principal','Cuidador Principal'),('cuidador_extra','Cuidador Adicional'),('admin','Administrador')], default='cuidador_principal', max_length=25)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='usuarios/fotos/')),
                ('fuente_grande', models.BooleanField(default=False)),
                ('alto_contraste', models.BooleanField(default=False)),
                ('notif_push', models.BooleanField(default=True)),
                ('notif_sms', models.BooleanField(default=True)),
                ('fcm_token', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('groups', models.ManyToManyField(blank=True, related_name='usuario_set', to='auth.group')),
                ('user_permissions', models.ManyToManyField(blank=True, related_name='usuario_set', to='auth.permission')),
            ],
            options={'verbose_name': 'Usuario', 'verbose_name_plural': 'Usuarios'},
        ),
        migrations.CreateModel(
            name='OTPVerificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telefono', models.CharField(max_length=20)),
                ('codigo', models.CharField(max_length=6)),
                ('intentos', models.PositiveIntegerField(default=0)),
                ('usado', models.BooleanField(default=False)),
                ('creado_at', models.DateTimeField(auto_now_add=True)),
                ('expira_at', models.DateTimeField()),
            ],
            options={'verbose_name': 'Verificación OTP'},
        ),
    ]
