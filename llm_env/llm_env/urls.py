from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    # 루트 경로("/")로 접속 시 바로 /evaluation/ 페이지로 이동
    path('', lambda request: redirect('evaluation/', permanent=False)), 

    path('admin/', admin.site.urls),

    # 'accounts/' 경로를 'users.urls'에 연결합니다. (수정된 부분)
    path('accounts/', include('users.urls')), 

    path('inference/', include('inference.urls')),
    path('evaluation/', include('evaluation.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)