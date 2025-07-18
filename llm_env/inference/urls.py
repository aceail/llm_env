# inference/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # views.inference_form 을 views.InferenceView.as_view() 로 변경
    path('', views.InferenceView.as_view(), name='inference_form'),
    path('upload_csv/', views.UploadCsvView.as_view(), name='upload_csv'), # 이 부분을 추가해주세요.
]