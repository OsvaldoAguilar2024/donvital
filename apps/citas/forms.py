from django import forms
from .models import Cita, Especialidad


class CitaForm(forms.ModelForm):
    def __init__(self, *args, pacientes=None, **kwargs):
        super().__init__(*args, **kwargs)
        if pacientes is not None:
            self.fields['paciente'].queryset = pacientes

    class Meta:
        model = Cita
        fields = [
            'paciente', 'especialidad', 'medico', 'fecha', 'hora',
            'lugar', 'direccion', 'documentos_requeridos', 'notas'
        ]
        widgets = {
            'paciente': forms.Select(attrs={'class': 'form-input'}),
            'especialidad': forms.Select(attrs={'class': 'form-input'}),
            'medico': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Dr. Nombre Apellido'}),
            'fecha': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'lugar': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Clínica / Hospital / IPS'}),
            'direccion': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Dirección completa'}),
            'documentos_requeridos': forms.Textarea(attrs={'class': 'form-input', 'rows': 2, 'placeholder': 'Carnet EPS, orden médica...'}),
            'notas': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
