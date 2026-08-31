from django.shortcuts import render, get_object_or_404
from .models import Country, Tour
from .forms import VisaCheckForm
from .services import get_visa_requirement

def country_view(request, slug):
    country = get_object_or_404(Country, slug=slug)
    tours = country.tours.all()

    return render(request, 'tours/country_detail.html', {
        'country': country,
        'tours': tours,
    })


def tour_view(request, slug):
    tour = get_object_or_404(Tour.objects.select_related('country').prefetch_related('images', 'dates', 'itinerary_days', 'inclusions'), slug=slug)

    form = VisaCheckForm(request.GET or None)
    visa_info = None

    if form.is_valid():
        user_citizenship = form.cleaned_data['citizenship']
        destination_code = tour.country.code
        
        visa_info = get_visa_requirement(user_citizenship, destination_code)

    context = {
        'tour': tour,
        'form': form,
        'visa_info': visa_info,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'tours/includes/visa_result.html', context)

    return render(request, 'tours/tour_detail.html', context)