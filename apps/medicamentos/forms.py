"""DON VITAL - Formularios de Medicamentos"""
from django import forms
from .models import Medicamento, RegistroToma


class MedicamentoForm(forms.ModelForm):
    # Horarios fijos como texto separado por comas
    horarios_texto = forms.CharField(
        required=False,
        label='Horarios de toma',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ej: 08:00, 14:00, 20:00',
        }),
        help_text='Ingresa los horarios separados por coma. Ej: 08:00, 14:00, 20:00'
    )

    # Días de la semana como checkboxes
    DIAS_CHOICES = [
        (0, 'Lun'), (1, 'Mar'), (2, 'Mié'),
        (3, 'Jue'), (4, 'Vie'), (5, 'Sáb'), (6, 'Dom'),
    ]
    dias_seleccionados = forms.MultipleChoiceField(
        choices=DIAS_CHOICES,
        required=False,
        label='Días de la semana',
        widget=forms.CheckboxSelectMultiple(),
    )

    class Meta:
        model = Medicamento
        fields = [
            'nombre', 'principio_activo', 'presentacion', 'dosis',
            'via_administracion', 'frecuencia_tipo', 'intervalo_horas',
            'instrucciones', 'medico_prescriptor', 'fecha_inicio', 'fecha_fin',
            'duracion_dias', 'foto_receta', 'numero_receta',
            'stock_actual', 'stock_minimo_alerta', 'fecha_vencimiento_medicamento',
            'requiere_renovacion_receta', 'fecha_vencimiento_receta',
            'dias_alerta_vencimiento_receta', 'estado', 'notas',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Metformina'}),
            'principio_activo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Metformina HCl'}),
            'presentacion': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Tableta 850mg'}),
            'dosis': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 1 tableta'}),
            'via_administracion': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Oral'}),
            'frecuencia_tipo': forms.Select(attrs={'class': 'form-input', 'id': 'id_frecuencia_tipo'}),
            'intervalo_horas': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 8', 'min': 1, 'max': 72}),
            'instrucciones': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Tomar con comida, no mezclar con...'}),
            'medico_prescriptor': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Dr. Nombre Apellido'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'duracion_dias': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Dejar vacío si es indefinido'}),
            'numero_receta': forms.TextInput(attrs={'class': 'form-input'}),
            'stock_actual': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 30'}),
            'stock_minimo_alerta': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 7'}),
            'fecha_vencimiento_medicamento': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'fecha_vencimiento_receta': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'dias_alerta_vencimiento_receta': forms.NumberInput(attrs={'class': 'form-input'}),
            'estado': forms.Select(attrs={'class': 'form-input'}),
            'notas': forms.Textarea(attrs={'class': 'form-input', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-poblar campos desde instancia
        if self.instance and self.instance.pk:
            if self.instance.horarios_fijos:
                self.fields['horarios_texto'].initial = ', '.join(self.instance.horarios_fijos)
            if self.instance.dias_semana:
                self.fields['dias_seleccionados'].initial = [str(d) for d in self.instance.dias_semana]

    def clean(self):
        cleaned = super().clean()
        freq = cleaned.get('frecuencia_tipo')

        if freq == Medicamento.FREQ_CADA_HORAS:
            if not cleaned.get('intervalo_horas'):
                self.add_error('intervalo_horas', 'Debes indicar el intervalo en horas.')

        elif freq == Medicamento.FREQ_VECES_DIA:
            horarios_texto = cleaned.get('horarios_texto', '')
            if not horarios_texto.strip():
                self.add_error('horarios_texto', 'Debes indicar al menos un horario.')

        elif freq == Medicamento.FREQ_DIAS_ESPECIFICOS:
            if not cleaned.get('dias_seleccionados'):
                self.add_error('dias_seleccionados', 'Debes seleccionar al menos un día.')

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        freq = self.cleaned_data.get('frecuencia_tipo')

        if freq == Medicamento.FREQ_VECES_DIA:
            horarios_texto = self.cleaned_data.get('horarios_texto', '')
            horarios = [h.strip() for h in horarios_texto.split(',') if h.strip()]
            instance.horarios_fijos = horarios
            instance.dias_semana = []
        elif freq == Medicamento.FREQ_DIAS_ESPECIFICOS:
            instance.dias_semana = [int(d) for d in self.cleaned_data.get('dias_seleccionados', [])]
            instance.horarios_fijos = []
        else:
            instance.horarios_fijos = []
            instance.dias_semana = []

        if commit:
            instance.save()
        return instance


class ConfirmarTomaForm(forms.Form):
    notas = forms.CharField(
        required=False,
        max_length=200,
        label='Observaciones (opcional)',
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Ej: Lo tomó con dificultad, náuseas leves...'
        })
    )
