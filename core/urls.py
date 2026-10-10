from django.urls import path
from .views import*

urlpatterns = [
    path("", home_view, name="home"),
    path("about/", about_page, name="about"),
    
    path('set-currency/', set_currency, name='set_currency'),
]