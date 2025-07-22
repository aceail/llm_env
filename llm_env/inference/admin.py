from django.contrib import admin
from .models import InferenceResult # InferenceResult 모델을 임포트합니다.

# Register your models here.

# 아래 코드를 추가해주세요.
@admin.register(InferenceResult)
class InferenceResultAdmin(admin.ModelAdmin):
    """
    InferenceResult 모델을 위한 Admin 페이지 설정
    """
    list_display = ('id', 'solution_name', 'user_prompt', 'created_at') # 목록에 보여줄 필드를 지정합니다.
    list_filter = ('solution_name', 'created_at') # 필터링할 필드를 지정합니다.
    search_fields = ('solution_name', 'user_prompt') # 검색할 필드를 지정합니다.