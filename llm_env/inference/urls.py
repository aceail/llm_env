# llm_env/inference/urls.py

from django.urls import path
from .views import UploadCsvView, UploadZipView, InferenceView
# 제가 이전에 EvaluationView를 이 파일에 추가하라고 안내드렸을 수 있으나,
# evaluation 앱으로 옮기는 것이 더 정확한 구조입니다.
# from .views import EvaluationView 

app_name = 'inference'
urlpatterns = [
    path('upload/', UploadCsvView.as_view(), name='upload_csv'),
    path('upload_zip/', UploadZipView.as_view(), name='upload_zip'),
    
    # ▼▼▼ 아래 줄에서 name='inference'를 name='inference_form'으로 수정합니다. ▼▼▼
    path('inference/', InferenceView.as_view(), name='inference_form'),
    # ▲▲▲ name='inference_form'으로 수정 ▲▲▲
]