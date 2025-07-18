from django.urls import path
from . import views

urlpatterns = [
    path('', views.inference_form, name='inference_form'),
    path('run/', views.run_inference, name='run_inference'),
]
