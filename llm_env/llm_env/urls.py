# llm_env/llm_env/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    # ▼▼▼ 아래 줄을 수정하세요. ▼▼▼
    # 루트 경로("/")로 접속 시 바로 /accounts/login/ 페이지로 이동
    path('', lambda request: redirect('accounts/login/', permanent=False)),
    # ▲▲▲ 위 줄을 수정하세요. ▲▲▲

    path('admin/', admin.site.urls),
    path('accounts/', include('users.urls')), 
    path('inference/', include('inference.urls')),
    path('evaluation/', include('evaluation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)