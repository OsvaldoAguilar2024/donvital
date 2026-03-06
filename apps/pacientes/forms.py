from django import forms
from .models import Paciente


class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = [
            'nombre', 'cedula', 'fecha_nacimiento', 'telefono', 'eps', 'numero_afiliacion',
            'grupo_sanguineo', 'alergias', 'medicamentos_actuales',
            'condiciones', 'contacto_emergencia', 'telefono_emergencia',
            'foto', 'foto_carnet_eps', 'notas'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre completo'}),
            'cedula': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: 12345678', 'inputmode': 'numeric'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'telefono': forms.TextInput(attrs={'class': 'form-input', 'inputmode': 'tel'}),
            'eps': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: Sura, Compensar'}),
            'numero_afiliacion': forms.TextInput(attrs={'class': 'form-input'}),
            'grupo_sanguineo': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ej: O+'}),
            'alergias': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'medicamentos_actuales': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'condiciones': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-input'}),
            'telefono_emergencia': forms.TextInput(attrs={'class': 'form-input', 'inputmode': 'tel'}),
            'notas': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class AsignarCuidadorForm(forms.Form):
    telefono = forms.CharField(
        label='Teléfono del cuidador', max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-input', 'inputmode': 'tel', 'placeholder': '+573001234567'})
    )
    rol = forms.ChoiceField(
        choices=[('principal', 'Cuidador Principal'), ('extra', 'Cuidador Adicional')],
        widget=forms.Select(attrs={'class': 'form-input'})
    )
