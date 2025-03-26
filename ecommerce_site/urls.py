from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView
from store.views import register, CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),  # Include store app URLs
    path('login/', CustomLoginView.as_view(template_name='store/login.html'), name='login'),
    path('register/', register, name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),
]

# ✅ Serve media files **only in DEBUG mode**
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
