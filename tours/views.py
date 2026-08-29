from django.shortcuts import render, get_object_or_404
from .models import Country, Tour

def country_view(request, slug):
    country = get_object_or_404(Country, slug=slug)
    tours = country.tours.all()

    return render(request, 'tours/country_detail.html', {
        'country': country,
        'tours': tours,
    })