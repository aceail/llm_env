from django.contrib import admin
from .models import Evaluation # Evaluation 모델을 임포트합니다.

# Register your models here.

# 아래 코드를 추가해주세요.
@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """
    Evaluation 모델을 위한 Admin 페이지 설정
    """
    list_display = ('id', 'inference_result', 'evaluator', 'agreement', 'quality', 'created_at') # 목록에 보여줄 필드를 지정합니다.
    list_filter = ('agreement', 'quality', 'evaluator') # 필터링할 필드를 지정합니다.
    search_fields = ('inference_result__solution_name', 'evaluator__username') # 관련된 모델의 필드로도 검색할 수 있습니다.