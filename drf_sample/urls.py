from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),

    path("api/v1/", include(("api.urls", "api"), namespace="api_v1")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
