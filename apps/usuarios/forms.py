"""DON VITAL - Formularios de Usuarios"""
from django import forms
from .models import Usuario


class TelefonoLoginForm(forms.Form):
    telefono = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '+57 300 000 0000',
            'inputmode': 'tel',
            'autocomplete': 'tel',
            'class': 'form-input',
        }),
        label='Tu número de teléfono'
    )

    def clean_telefono(self):
        tel = self.cleaned_data['telefono'].strip().replace(' ', '').replace('-', '')
        if not tel.startswith('+'):
            tel = '+57' + tel.lstrip('0')
        return tel


class OTPVerificacionForm(forms.Form):
    codigo = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': '123456',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'class': 'form-input otp-input',
            'maxlength': '6',
        }),
        label='Código de verificación'
    )


class RegistroForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'telefono', 'email', 'rol']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Tu nombre completo'}),
            'telefono': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+57 300 000 0000', 'inputmode': 'tel'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'opcional@email.com'}),
            'rol': forms.Select(attrs={'class': 'form-input'}),
        }

    def clean_telefono(self):
        tel = self.cleaned_data['telefono'].strip().replace(' ', '').replace('-', '')
        if not tel.startswith('+'):
            tel = '+57' + tel.lstrip('0')
        return tel


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'email', 'foto', 'fuente_grande', 'alto_contraste', 'notif_push', 'notif_sms']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
        }
