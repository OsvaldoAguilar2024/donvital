from django import forms
from .models import Usuario


class RegistroForm(forms.ModelForm):
    password = forms.CharField(
    label='Contraseña',
    widget=forms.PasswordInput(attrs={
        'class': 'form-input',
        'placeholder': 'Mínimo 6 caracteres'
    }),
    min_length=6,
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
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmar = cleaned_data.get('confirmar_password')
        if password and confirmar and password != confirmar:
            raise forms.ValidationError('Las contraseñas no coinciden.')
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
