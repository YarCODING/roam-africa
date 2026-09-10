from django import forms
from .models import Booking
from tours.models import TourDate
from datetime import timedelta
from django.utils import timezone

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'tour_date', 
            'customer_name', 
            'customer_phone', 
            'customer_email', 
            'persons_count', 
            'comment'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'input input-bordered w-full rounded-xl'}),
            'customer_phone': forms.TextInput(attrs={'class': 'input input-bordered w-full rounded-xl', 'placeholder': '+380...'}),
            'customer_email': forms.EmailInput(attrs={'class': 'input validator input-bordered w-full rounded-xl'}),
            'persons_count': forms.NumberInput(attrs={'class': 'input input-bordered w-full rounded-xl', 'min': 1}),
            'comment': forms.Textarea(attrs={'class': 'textarea textarea-bordered w-full rounded-xl', 'rows': 3}),
            'tour_date': forms.Select(attrs={'class': 'select select-bordered w-full rounded-xl'}),
        }

    def __init__(self, *args, tour=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tour:
            min_date = timezone.now().date() + timedelta(days=10)

            self.fields['tour_date'].queryset = TourDate.objects.filter(
                tour=tour,
                start_date__gte=min_date
            ).exclude(status__in=['sold_out', 'canceled'])