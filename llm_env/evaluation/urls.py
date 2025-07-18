from django.urls import path
from . import views

urlpatterns = [
    path('', views.evaluation_view, name='evaluation'),
    path('<int:pk>/', views.evaluation_view, name='evaluation_detail'),
]
