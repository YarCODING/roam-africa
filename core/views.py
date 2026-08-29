import json
from django.shortcuts import render
from django.urls import reverse
from tours.models import Country

def home_view(request):
    countries = Country.objects.all()
    
    countries_data = {
        country.code: {
            "name": country.name,
            "url": reverse("country_detail", kwargs={"slug": country.slug}) if hasattr(country, 'slug') else "#",
            "image": country.cover_image.url if country.cover_image else None,
            "description": country.description[:100] + "..." if country.description else ""
        }
        for country in countries
    }

    reviews = [
            {
                "author": "Олена Ковальчук",
                "country": "Танзанія",
                "text": "Сафарі в парку Тарангіре — це щось неймовірне! Побачити диких слонів так близько прямо з відкритого джипа було моєю мрією. Дякую агенції за ідеальну організацію!",
                "image": "review1.jpg"
            },
            {
                "author": "Максим Бойко",
                "country": "Танзанія",
                "text": "Вид на Кіліманджаро на світанку просто перехоплює подих. Дякую турагенції за чіткий маршрут, крутий готель з видом на вулкан та турботу про кожну деталь нашої подорожі!",
                "image": "review2.jpg"
            },
            {
                "author": "Юлія Мельник",
                "country": "Єгипет (Сива)",
                "text": "Плавання у соляних озерах оазису Сива в Єгипті — це космічні відчуття! Вода тримає сама, а пейзажі навколо просто заворожують. Нереальний релакс і незабутні враження!",
                "image": "review3.jpg"
            },
            {
                "author": "Дарина Ткаченко",
                "country": "Кенія",
                "text": "Прогулянка саваною серед зебр та безкрайніх пейзажів Кенії. Повна свобода, чисте повітря та дика природа — Африка назавжди підкорила моє серце. Обов'язково повернуся ще!",
                "image": "review4.jpg"
            },
            {
                "author": "Ірина Кравченко",
                "country": "Марокко",
                "text": "Синє місто Шефшауен у Марокко — це справжня казка наяву! Кожна вуличка наче з картинки. Величезне дякую турагенції за насичену програму та комфортний трансфер!",
                "image": "review5.jpg"
            },
        ]

    context = {
        "countries_json": json.dumps(countries_data),
        "reviews": reviews
    }

    
    return render(request, "core/home.html", context)