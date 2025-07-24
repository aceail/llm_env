from django.db import models
from django.conf import settings
from inference.models import InferenceResult

# Create your models here.

# ▼▼▼ 아래 클래스를 파일에 추가해주세요. ▼▼▼
class Evaluation(models.Model):
    # 어떤 추론 결과에 대한 평가인지 연결합니다.
    inference_result = models.ForeignKey(InferenceResult, on_delete=models.CASCADE, related_name='evaluations')
    
    # 누가 평가했는지 사용자 정보와 연결합니다.
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # 평가 데이터 필드
    agreement = models.CharField(max_length=1, choices=[('O', 'O'), ('X', 'X')])
    quality = models.IntegerField()  # 1점에서 5점까지 저장
    comment = models.TextField(blank=True) # 코멘트는 비어있을 수 있음
    lesion_vessel = models.CharField(max_length=255, blank=True, default="")
    lesion_anatomic = models.CharField(max_length=255, blank=True, default="")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for {self.inference_result.id} by {self.evaluator.username}"

