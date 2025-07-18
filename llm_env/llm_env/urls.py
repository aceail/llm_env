# llm_env/llm_env/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 아래 라인을 주석 처리해주세요.
    # path('accounts/', include('accounts.urls')), 
    
    path('inference/', include('inference.urls')),
    path('evaluation/', include('evaluation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)