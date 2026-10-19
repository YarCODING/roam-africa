from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm
from turnstile.fields import TurnstileField
from django.forms import ModelForm
from django import forms
from .models import CustomUser

class ProfileForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ['image', 'displayname', 'info']
        labels = {
            'image': 'Аватар',
            'displayname': 'Відображуване ім’я',
            'info': 'Про себе',
        }
        widgets = {
            'image': forms.FileInput(attrs={'class': 'file-input file-input-bordered w-full my-1'}),
            'displayname': forms.TextInput(attrs={'placeholder': 'Введіть ім’я', 'class': 'input input-bordered w-full my-1'}),
            'info': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Розкажіть про себе', 'class': 'textarea textarea-bordered w-full my-1'})
        }
        
class EmailForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        error_messages={
            'required': 'Це поле є обов\'язковим.',
            'invalid': 'Введіть коректну електронну адресу.',
        },
        widget=forms.EmailInput(attrs={
            'class': 'input input-bordered input-sm sm:input-md w-full',
            'placeholder': 'Введіть нову пошту'
        })
    )

    class Meta:
        model = CustomUser
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data.get('email')

        queryset = CustomUser.objects.filter(email=email)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
            
        if queryset.exists():
            raise ValidationError("Ця електронна адреса вже використовується іншим користувачем.")
            
        return email


class CustomSignupForm(SignupForm):
    turnstile = TurnstileField(label="")

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request:
            client_ip = self.request.META.get('REMOTE_ADDR')
            if client_ip and 'turnstile' in self.fields:
                self.fields['turnstile'].remote_ip = client_ip

    def visible_fields(self):
        return [field for field in super().visible_fields() if field.name != 'turnstile']