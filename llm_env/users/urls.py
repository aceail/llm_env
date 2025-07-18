# llm_env/users/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # signup 경로를 삭제합니다.
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]