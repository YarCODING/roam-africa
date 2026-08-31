# forms.py
from django import forms
from django_countries import countries

class VisaCheckForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        sorted_countries = sorted(countries, key=lambda c: c.name)
        self.fields['citizenship'].choices = [('', 'Оберіть громадянство...')] + sorted_countries

    citizenship = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'select select-bordered w-full focus:select-primary',
            'hx-get': '',
            'hx-target': '#visa-result-container',
            'hx-trigger': 'change',
            'hx-indicator': '#visa-loader',
        }),
        label="Ваше громадянство"
    )