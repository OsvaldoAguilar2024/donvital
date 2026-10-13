"""Pruebas de la Fase 0: accesos, ingreso, portal del paciente y horarios."""
from datetime import date, datetime, time, timedelta
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.citas.models import Cita
from apps.medicamentos.models import Medicamento, RegistroToma
from apps.pacientes.models import CuidadorPaciente, Paciente
from apps.usuarios.models import OTPVerificacion, Usuario

CLAVE = 'Clave-Segura-2026'


def crear_cuidador(tel, nombre='Cuidador'):
    return Usuario.objects.create_user(telefono=tel, nombre=nombre, password=CLAVE)


def crear_paciente(cuidador, nombre='Rosa', cedula='', pin=None):
    p = Paciente(nombre=nombre, cedula=cedula)
    if pin:
        p.set_pin(pin)
    p.save()
    CuidadorPaciente.objects.create(usuario=cuidador, paciente=p, rol='principal')
    return p


class Base(TestCase):
    def setUp(self):
        cache.clear()
        self.ana = crear_cuidador('+573001111111', 'Ana')
        self.beto = crear_cuidador('+573002222222', 'Beto')
        self.rosa = crear_paciente(self.ana, 'Rosa', '1001', pin='4826')  # paciente de Ana


class RegistroTests(Base):
    def test_no_permite_registrarse_como_admin(self):
        r = self.client.post('/usuarios/registro/', {
            'nombre': 'Intruso', 'telefono': '3009999999', 'rol': 'admin',
            'password': CLAVE, 'confirmar_password': CLAVE,
        })
        self.assertEqual(r.status_code, 200)  # el formulario se rechaza
        self.assertFalse(Usuario.objects.filter(nombre='Intruso').exists())

    def test_rol_admin_en_base_no_da_acceso_a_todo(self):
        self.beto.rol = 'admin'
        self.beto.save()
        self.client.force_login(self.beto)
        r = self.client.get('/pacientes/')
        self.assertNotContains(r, 'Rosa')

    def test_registro_normal_funciona_y_normaliza_telefono(self):
        r = self.client.post('/usuarios/registro/', {
            'nombre': 'Laura', 'telefono': '300 333 3333', 'rol': 'cuidador_principal',
            'password': CLAVE, 'confirmar_password': CLAVE,
        })
        self.assertRedirects(r, '/usuarios/login/')
        self.assertTrue(Usuario.objects.filter(telefono='+573003333333').exists())

    def test_rechaza_contrasena_debil(self):
        self.client.post('/usuarios/registro/', {
            'nombre': 'Debil', 'telefono': '3004444444', 'rol': 'cuidador_principal',
            'password': '12345678', 'confirmar_password': '12345678',
        })
        self.assertFalse(Usuario.objects.filter(nombre='Debil').exists())


class AccesoPacientesAjenosTests(Base):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.beto)  # Beto NO cuida a Rosa

    def test_no_ve_paciente_ajeno(self):
        r = self.client.get(f'/pacientes/{self.rosa.id}/')
        self.assertRedirects(r, '/pacientes/')

    def test_no_edita_paciente_ajeno(self):
        self.client.post(f'/pacientes/{self.rosa.id}/editar/', {'nombre': 'Hackeado'})
        self.rosa.refresh_from_db()
        self.assertEqual(self.rosa.nombre, 'Rosa')

    def test_no_crea_medicamento_a_paciente_ajeno(self):
        self.client.post('/medicamentos/nuevo/', {
            'paciente': self.rosa.id, 'nombre': 'X', 'dosis': '1', 'frecuencia_tipo': 'veces_dia',
            'horarios_texto': '08:00', 'fecha_inicio': '2026-10-01', 'estado': 'activo',
            'dias_alerta_vencimiento_receta': 7,
        })
        self.assertFalse(Medicamento.objects.filter(paciente=self.rosa).exists())

    def test_no_cancela_ni_confirma_cita_ajena(self):
        cita = Cita.objects.create(paciente=self.rosa, fecha=date(2026, 12, 1), hora=time(9, 0))
        self.client.post(f'/citas/{cita.id}/cancelar/')
        self.client.post(f'/citas/{cita.id}/confirmar/')
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'programada')

    def test_cancelar_cita_no_funciona_por_enlace(self):
        self.client.force_login(self.ana)
        cita = Cita.objects.create(paciente=self.rosa, fecha=date(2026, 12, 1), hora=time(9, 0))
        r = self.client.get(f'/citas/{cita.id}/cancelar/')
        self.assertEqual(r.status_code, 405)
        cita.refresh_from_db()
        self.assertEqual(cita.estado, 'programada')

    def test_el_cuidador_si_puede(self):
        self.client.force_login(self.ana)
        r = self.client.get(f'/pacientes/{self.rosa.id}/')
        self.assertEqual(r.status_code, 200)


@override_settings(DEBUG=False, TWILIO_ACCOUNT_SID='')
class IngresoTests(Base):
    def test_login_contrasena_y_mensaje_generico(self):
        r = self.client.post('/usuarios/login/', {'telefono': '3001111111', 'metodo': 'password', 'password': CLAVE})
        self.assertRedirects(r, '/dashboard/', fetch_redirect_response=False)
        self.client.logout()
        r1 = self.client.post('/usuarios/login/', {'telefono': '3001111111', 'metodo': 'password', 'password': 'mala'})
        r2 = self.client.post('/usuarios/login/', {'telefono': '3007777777', 'metodo': 'password', 'password': 'mala'})
        self.assertContains(r1, 'Número o contraseña incorrectos')
        self.assertContains(r2, 'Número o contraseña incorrectos')

    def test_bloqueo_por_intentos_de_contrasena(self):
        for _ in range(5):
            self.client.post('/usuarios/login/', {'telefono': '3001111111', 'metodo': 'password', 'password': 'mala'})
        r = self.client.post('/usuarios/login/', {'telefono': '3001111111', 'metodo': 'password', 'password': CLAVE})
        self.assertEqual(r.status_code, 429)

    def _pedir_codigo(self, codigo='123456'):
        with mock.patch('apps.usuarios.views.generar_otp', return_value=codigo), \
             mock.patch('apps.notificaciones.services.enviar_sms_otp', return_value=False):
            return self.client.post('/usuarios/login/', {'telefono': '3001111111', 'metodo': 'otp'}, follow=True)

    def test_codigo_sms_funciona_y_no_se_muestra_en_pantalla(self):
        r = self._pedir_codigo('123456')
        self.assertNotContains(r, '123456')  # antes se mostraba si Twilio fallaba
        otp = OTPVerificacion.objects.get(telefono='+573001111111')
        self.assertNotEqual(otp.codigo, '123456')  # guardado cifrado
        r = self.client.post('/usuarios/otp/', {'codigo': '123456'})
        self.assertRedirects(r, '/dashboard/', fetch_redirect_response=False)

    def test_codigo_sms_se_bloquea_tras_3_intentos(self):
        self._pedir_codigo('123456')
        for _ in range(3):
            self.client.post('/usuarios/otp/', {'codigo': '000000'})
        r = self.client.post('/usuarios/otp/', {'codigo': '123456'})
        self.assertNotEqual(r.get('Location'), '/dashboard/')
        self.assertFalse('_auth_user_id' in self.client.session)

    def test_numero_no_registrado_no_se_revela(self):
        r = self.client.post('/usuarios/login/', {'telefono': '3008888888', 'metodo': 'otp'}, follow=True)
        self.assertContains(r, 'Si el número está registrado')


class PortalPacienteTests(Base):
    def test_solo_cedula_ya_no_basta(self):
        r = self.client.post('/paciente/', {'cedula': '1001'})
        self.assertNotIn('paciente_id', self.client.session)
        self.assertEqual(r.status_code, 200)

    def test_cedula_y_pin_correctos(self):
        r = self.client.post('/paciente/', {'cedula': '1.001', 'pin': '4826'})
        self.assertRedirects(r, '/paciente/inicio/', fetch_redirect_response=False)

    def test_bloqueo_tras_5_pin_errados(self):
        for _ in range(5):
            self.client.post('/paciente/', {'cedula': '1001', 'pin': '0000'})
        r = self.client.post('/paciente/', {'cedula': '1001', 'pin': '4826'})
        self.assertEqual(r.status_code, 429)
        self.assertNotIn('paciente_id', self.client.session)

    def test_emergencia_limitada_a_una_cada_5_minutos(self):
        self.client.post('/paciente/', {'cedula': '1001', 'pin': '4826'})
        with mock.patch('apps.notificaciones.services.enviar_sms', return_value=True) as sms:
            self.client.post('/paciente/emergencia/', {'latitud': '4.6', 'longitud': '-74.08'})
            self.client.post('/paciente/emergencia/', {'latitud': '4.6', 'longitud': '-74.08'})
        self.assertEqual(sms.call_count, 1)

    def test_emergencia_ignora_coordenadas_invalidas(self):
        self.client.post('/paciente/', {'cedula': '1001', 'pin': '4826'})
        with mock.patch('apps.notificaciones.services.enviar_sms', return_value=True) as sms:
            self.client.post('/paciente/emergencia/', {'latitud': 'x', 'longitud': 'http://malo'})
        self.assertIn('No se pudo obtener ubicación', sms.call_args[0][1])


class HorariosTests(Base):
    """Las tomas se programan en hora de Colombia (UTC-5)."""

    def setUp(self):
        super().setUp()
        self.med = Medicamento.objects.create(
            paciente=self.rosa, nombre='Metformina', dosis='1 tableta',
            frecuencia_tipo='veces_dia', horarios_fijos=['08:00', '23:55'],
            fecha_inicio=date(2026, 10, 1),
        )

    def _en(self, y, m, d, h, mi):
        """Momento en hora de Colombia, convertido a UTC como lo da el servidor."""
        tz = timezone.get_current_timezone()
        return timezone.make_aware(datetime(y, m, d, h, mi), tz)

    def test_recordatorio_de_las_8_sale_a_las_8_hora_colombia(self):
        from apps.medicamentos.tasks import generar_registros_toma_diarios, verificar_y_enviar_tomas
        generar_registros_toma_diarios(hoy=date(2026, 10, 13))
        with mock.patch('apps.medicamentos.tasks.enviar_recordatorio_medicamento') as enviar:
            # 8:00 am en Colombia = 13:00 UTC
            r = verificar_y_enviar_tomas(ahora=self._en(2026, 10, 13, 8, 0))
        self.assertEqual(r['enviados'], 1)
        enviar.assert_called_once()

    def test_a_la_1pm_no_se_envia_la_de_las_8(self):
        from apps.medicamentos.tasks import generar_registros_toma_diarios, verificar_y_enviar_tomas
        generar_registros_toma_diarios(hoy=date(2026, 10, 13))
        with mock.patch('apps.medicamentos.tasks.enviar_recordatorio_medicamento'):
            r = verificar_y_enviar_tomas(ahora=self._en(2026, 10, 13, 13, 0))
        self.assertEqual(r['enviados'], 0)

    def test_ventana_cruza_medianoche(self):
        from apps.medicamentos.tasks import generar_registros_toma_diarios, verificar_y_enviar_tomas
        generar_registros_toma_diarios(hoy=date(2026, 10, 13))
        with mock.patch('apps.medicamentos.tasks.enviar_recordatorio_medicamento') as enviar:
            r = verificar_y_enviar_tomas(ahora=self._en(2026, 10, 14, 0, 10))  # la de 23:55 del día anterior
        self.assertEqual(r['enviados'], 1)
        toma = RegistroToma.objects.get(id=enviar.call_args[0][0])
        self.assertEqual(toma.hora_programada, time(23, 55))

    def test_hoy_es_la_fecha_de_colombia_en_la_noche(self):
        # 9:30 pm del 13 en Colombia = 02:30 UTC del 14
        with mock.patch('django.utils.timezone.now', return_value=self._en(2026, 10, 13, 21, 30)):
            self.assertEqual(timezone.localdate(), date(2026, 10, 13))

    def test_comando_de_cron_corre_completo(self):
        from django.core.management import call_command
        from io import StringIO
        out = StringIO()
        with mock.patch('apps.notificaciones.services.enviar_sms', return_value=True):
            call_command('enviar_recordatorios', stdout=out)
        self.assertIn('Tomas creadas', out.getvalue())


class PantallasTests(Base):
    """Recorrido por las pantallas principales: ninguna debe fallar."""

    def test_pantallas_cuidador(self):
        self.client.force_login(self.ana)
        Medicamento.objects.create(paciente=self.rosa, nombre='Losartán', dosis='1', frecuencia_tipo='veces_dia',
                                   horarios_fijos=['08:00'], fecha_inicio=date(2026, 10, 1))
        cita = Cita.objects.create(paciente=self.rosa, fecha=date(2026, 12, 1), hora=time(9, 0))
        for url in ['/dashboard/', '/pacientes/', f'/pacientes/{self.rosa.id}/', f'/pacientes/{self.rosa.id}/editar/',
                    '/pacientes/nuevo/', '/medicamentos/', '/medicamentos/hoy/', '/medicamentos/nuevo/',
                    '/citas/', '/citas/nueva/', f'/citas/{cita.id}/', '/notificaciones/', '/usuarios/perfil/',
                    '/suscripciones/mi-plan/']:
            r = self.client.get(url)
            self.assertIn(r.status_code, (200, 302), url)
        r = self.client.post('/notificaciones/leer-todas/')
        self.assertEqual(r.status_code, 302)

    def test_pantallas_publicas(self):
        for url in ['/usuarios/login/', '/usuarios/registro/', '/paciente/']:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.client.post('/paciente/', {'cedula': '1001', 'pin': '4826'})
        self.assertEqual(self.client.get('/paciente/inicio/').status_code, 200)

    def test_editar_paciente_cambia_pin(self):
        self.client.force_login(self.ana)
        r = self.client.post(f'/pacientes/{self.rosa.id}/editar/', {
            'nombre': 'Rosa', 'cedula': '1001', 'fecha_nacimiento': '1950-03-02', 'pin_nuevo': '7391'})
        self.rosa.refresh_from_db()
        self.assertTrue(self.rosa.check_pin('7391'), r.content[:300])
