from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('nodecost/', include('nodecost.urls')),  # アプリケーション nodecost のURLをインクルード
]
