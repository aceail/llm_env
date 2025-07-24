# llm_env/evaluation/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.evaluation_list, name='evaluation'),
    path('<int:pk>/', views.evaluation_detail, name='evaluation_detail'),
    path('delete/<int:pk>/', views.delete_inference, name='delete_inference'),
    path('delete_all/', views.delete_all_inferences, name='delete_all_inferences'), # 이 부분을 추가해주세요.
    path('download/', views.download_paired_results, name='download_paired_results'),
    path('submit_evaluation/<int:pk>/', views.submit_evaluation, name='submit_evaluation'),

]