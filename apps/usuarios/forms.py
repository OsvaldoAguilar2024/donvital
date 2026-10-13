from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import Usuario

# Roles que alguien puede escoger al registrarse. "Administrador" NUNCA es público.
ROLES_REGISTRO = [
    (Usuario.ROL_CUIDADOR_PRINCIPAL, 'Cuidador Principal'),
    (Usuario.ROL_CUIDADOR_EXTRA, 'Cuidador Adicional'),
    (Usuario.ROL_PACIENTE, 'Paciente'),
]


class RegistroForm(forms.ModelForm):
    password = forms.CharField(
    label='Contraseña',
    widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Mínimo 8 caracteres'
    }),
    min_length=8,
    required=True
    )
    confirmar_password = forms.CharField(
    label='Confirmar contraseña',
    widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Repite tu contraseña'
    }),
    required=True
    )
    rol = forms.ChoiceField(
        choices=ROLES_REGISTRO,
        initial=Usuario.ROL_CUIDADOR_PRINCIPAL,
        widget=forms.Select(attrs={'class': 'form-input'}),
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'telefono', 'rol']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Tu nombre completo'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '+573001234567'
            }),
            'rol': forms.Select(attrs={
                'class': 'form-input'
            }),
        }
    def clean_telefono(self):
        from apps.notificaciones.services import normalizar_telefono
        tel = normalizar_telefono(self.cleaned_data.get('telefono', ''))
        if not tel[1:].isdigit() or not (11 <= len(tel) <= 16):
            raise forms.ValidationError('Número de celular no válido. Ej: 3001234567')
        if Usuario.objects.filter(telefono=tel).exists():
            raise forms.ValidationError('Ya existe una cuenta con este número.')
        return tel

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmar = cleaned_data.get('confirmar_password')
        if password and confirmar and password != confirmar:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        if password:
            try:
                validate_password(password)
            except forms.ValidationError as e:
                self.add_error('password', e)
        return cleaned_data


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'email']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg'
            }),
        }
