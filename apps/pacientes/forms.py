from django import forms
from .models import Paciente


class PacienteForm(forms.ModelForm):
    pin_nuevo = forms.CharField(
        label='PIN del portal del paciente',
        required=False,
        min_length=4, max_length=6,
        help_text='4 a 6 dígitos. El paciente entra al portal con su cédula y este PIN. '
                  'Déjalo vacío para no cambiarlo.',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'inputmode': 'numeric',
                                          'autocomplete': 'new-password', 'placeholder': '••••'}),
    )

    def clean_pin_nuevo(self):
        pin = (self.cleaned_data.get('pin_nuevo') or '').strip()
        if pin and not pin.isdigit():
            raise forms.ValidationError('El PIN solo puede tener números.')
        if pin and len(set(pin)) == 1:
            raise forms.ValidationError('Usa un PIN que no repita el mismo número (ej. no 1111).')
        if pin and pin in '0123456789' :
            raise forms.ValidationError('Evita PIN consecutivos como 1234.')
        return pin

    def clean_cedula(self):
        cedula = (self.cleaned_data.get('cedula') or '').strip().replace(' ', '').replace('.', '')
        if cedula and not cedula.isdigit():
            raise forms.ValidationError('La cédula solo puede tener números.')
        return cedula

    def save(self, commit=True):
        paciente = super().save(commit=False)
        pin = self.cleaned_data.get('pin_nuevo')
        if pin:
            paciente.set_pin(pin)
            paciente.portal_intentos_fallidos = 0
            paciente.portal_bloqueado_hasta = None
        if commit:
            paciente.save()
        return paciente

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
