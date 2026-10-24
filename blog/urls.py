from django.urls import path
from . import views

urlpatterns = [
    path("", views.blog_list_view, name="blog_list"),
    path("<slug:slug>/", views.blog_detail_view, name="blog_detail"),
]