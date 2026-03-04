from django.db import models
from django.utils import timezone
from apps.pacientes.models import Paciente
from apps.usuarios.models import Usuario


class Medicamento(models.Model):
    FREQ_CADA_HORAS = 'cada_horas'
    FREQ_VECES_DIA = 'veces_dia'
    FREQ_DIAS_ESPECIFICOS = 'dias_esp'
    FREQ_SEGUN_NECESIDAD = 'necesidad'
    FRECUENCIAS = [
        (FREQ_CADA_HORAS,       'Cada X horas (ej: cada 8h)'),
        (FREQ_VECES_DIA,        'X veces al día en horarios fijos'),
        (FREQ_DIAS_ESPECIFICOS, 'Días específicos de la semana'),
        (FREQ_SEGUN_NECESIDAD,  'Solo cuando se necesite (SOS)'),
    ]

    ESTADO_ACTIVO = 'activo'
    ESTADO_PAUSADO = 'pausado'
    ESTADO_SUSPENDIDO = 'suspendido'
    ESTADOS = [
        (ESTADO_ACTIVO,     'Activo'),
        (ESTADO_PAUSADO,    'Pausado temporalmente'),
        (ESTADO_SUSPENDIDO, 'Suspendido'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='medicamentos')
    registrado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='medicamentos_registrados')

    nombre = models.CharField(max_length=200, verbose_name='Nombre del medicamento')
    principio_activo = models.CharField(max_length=200, blank=True)
    presentacion = models.CharField(max_length=100, blank=True, help_text='Ej: Tableta 500mg')
    dosis = models.CharField(max_length=100, verbose_name='Dosis por toma', help_text='Ej: 1 tableta, 5ml')
    via_administracion = models.CharField(max_length=80, blank=True)
    instrucciones = models.TextField(blank=True, help_text='Tomar con comida, evitar sol...')

    # Frecuencia configurable
    frecuencia_tipo = models.CharField(max_length=15, choices=FRECUENCIAS, default=FREQ_VECES_DIA)
    intervalo_horas = models.PositiveIntegerField(null=True, blank=True, help_text='Ej: 8 para cada 8 horas')
    horarios_fijos = models.JSONField(default=list, blank=True, help_text='["08:00","14:00","20:00"]')
    dias_semana = models.JSONField(default=list, blank=True, help_text='[0,1,2] donde 0=Lunes')

    # Prescripción
    medico_prescriptor = models.CharField(max_length=150, blank=True)
    fecha_inicio = models.DateField(verbose_name='Fecha inicio tratamiento')
    fecha_fin = models.DateField(null=True, blank=True)
    duracion_dias = models.PositiveIntegerField(null=True, blank=True)
    numero_receta = models.CharField(max_length=100, blank=True)
    foto_receta = models.ImageField(upload_to='medicamentos/recetas/', blank=True, null=True)

    # Stock
    stock_actual = models.PositiveIntegerField(null=True, blank=True)
    stock_minimo_alerta = models.PositiveIntegerField(null=True, blank=True)
    fecha_vencimiento_medicamento = models.DateField(null=True, blank=True)

    # Receta con renovación
    requiere_renovacion_receta = models.BooleanField(default=False)
    fecha_vencimiento_receta = models.DateField(null=True, blank=True)
    dias_alerta_vencimiento_receta = models.PositiveIntegerField(default=7)

    estado = models.CharField(max_length=15, choices=ESTADOS, default=ESTADO_ACTIVO)
    notas = models.TextField(blank=True)
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'
        ordering = ['paciente', 'nombre']

    def __str__(self):
        return f'{self.nombre} — {self.paciente.nombre} ({self.dosis})'

    @property
    def stock_bajo(self):
        if self.stock_actual is None or self.stock_minimo_alerta is None:
            return False
        return self.stock_actual <= self.stock_minimo_alerta

    @property
    def medicamento_vencido(self):
        if not self.fecha_vencimiento_medicamento:
            return False
        return self.fecha_vencimiento_medicamento < timezone.now().date()

    @property
    def receta_vencida(self):
        if not self.fecha_vencimiento_receta:
            return False
        return self.fecha_vencimiento_receta < timezone.now().date()

    @property
    def receta_vence_pronto(self):
        if not self.fecha_vencimiento_receta:
            return False
        dias = (self.fecha_vencimiento_receta - timezone.now().date()).days
        return 0 <= dias <= self.dias_alerta_vencimiento_receta

    def get_horarios_display(self):
        if self.frecuencia_tipo == self.FREQ_CADA_HORAS:
            return f'Cada {self.intervalo_horas} horas'
        elif self.frecuencia_tipo == self.FREQ_VECES_DIA:
            return ', '.join(self.horarios_fijos) if self.horarios_fijos else 'Sin horarios'
        elif self.frecuencia_tipo == self.FREQ_DIAS_ESPECIFICOS:
            nombres = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
            return ', '.join(nombres[d] for d in (self.dias_semana or []) if 0 <= d <= 6)
        return 'Según necesidad'


class RegistroToma(models.Model):
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_TOMADO = 'tomado'
    ESTADO_OMITIDO = 'omitido'
    ESTADO_RETRASADO = 'retrasado'
    ESTADOS = [
        (ESTADO_PENDIENTE,  '⏳ Pendiente'),
        (ESTADO_TOMADO,     '✅ Tomado'),
        (ESTADO_OMITIDO,    '❌ Omitido'),
        (ESTADO_RETRASADO,  '⚠️ Retrasado'),
    ]

    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE, related_name='registros_toma')
    fecha_programada = models.DateField()
    hora_programada = models.TimeField()
    estado = models.CharField(max_length=10, choices=ESTADOS, default=ESTADO_PENDIENTE)
    confirmado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='tomas_confirmadas')
    hora_real_toma = models.DateTimeField(null=True, blank=True)
    notas_toma = models.CharField(max_length=200, blank=True)
    unidades_consumidas = models.PositiveIntegerField(default=1)
    creado_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Registro de Toma'
        verbose_name_plural = 'Registros de Toma'
        ordering = ['-fecha_programada', '-hora_programada']
        unique_together = ['medicamento', 'fecha_programada', 'hora_programada']

    def __str__(self):
        return f'{self.medicamento.nombre} — {self.fecha_programada} {self.hora_programada}'

    def confirmar_toma(self, usuario, notas=''):
        self.estado = self.ESTADO_TOMADO
        self.confirmado_por = usuario
        self.hora_real_toma = timezone.now()
        self.notas_toma = notas
        self.save()
        med = self.medicamento
        if med.stock_actual is not None:
            med.stock_actual = max(0, med.stock_actual - self.unidades_consumidas)
            med.save(update_fields=['stock_actual'])

    def marcar_omitido(self, usuario, notas=''):
        self.estado = self.ESTADO_OMITIDO
        self.confirmado_por = usuario
        self.notas_toma = notas
        self.save()


class HistorialMedicamento(models.Model):
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE, related_name='historial')
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    accion = models.CharField(max_length=100)
    detalle = models.TextField(blank=True)
    creado_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historial Medicamento'
        ordering = ['-creado_at']

    def __str__(self):
        return f'{self.accion} — {self.medicamento.nombre}'
