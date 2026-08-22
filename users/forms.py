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
        
class EmailForm(ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ['email']