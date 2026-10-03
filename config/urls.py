from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import profile_view
from bookings.views import stripe_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('hijack/', include('hijack.urls')),
    path("", include("core.urls")),
    path('profile/', include('users.urls')),
    path("", include('tours.urls')),
    path('bookings/', include('bookings.urls')),
    path('webhooks/stripe/', stripe_webhook, name='stripe_webhook'),
    path('@<username>/', profile_view, name="profile"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]


admin.site.site_header = "Адміністрування Roam Africa"
admin.site.index_title = "Адміністрування контентом"
admin.site.site_title = "Панель керування"