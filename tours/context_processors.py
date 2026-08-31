from .models import Country


def countries_processor(request):
    return {'header_countries': Country.objects.all()}