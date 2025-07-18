"""
URL configuration for llm_env project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# llm_env/llm_env/urls.py

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('evaluation/', include('evaluation.urls')),
    path('inference/', include('inference.urls')),
    path('users/', include('users.urls')),  # users 앱 URL 추가
    path('', RedirectView.as_view(url='/evaluation/', permanent=True)), # 루트 경로 리다이렉트 추가
]