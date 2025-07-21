# llm_env/inference/models.py

from django.db import models
from django.contrib.auth.models import User

# 기존 모델 코드는 그대로 둡니다.
class InferenceResult(models.Model):
    # ▼▼▼ 아래 한 줄을 추가해주세요 ▼▼▼
    solution_name = models.CharField(max_length=255, blank=True, help_text="솔루션 이름")
    # ▲▲▲ 위 한 줄을 추가해주세요 ▲▲▲
    
    system_prompt = models.TextField(blank=True)
    user_prompt = models.TextField(blank=True)
    image_urls = models.JSONField(default=list, blank=True)
    llm_output = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # 이 필드가 있을 수도 있습니다.

    def __str__(self):
        return f"Result for {self.user_prompt[:30]} on {self.created_at.strftime('%Y-%m-%d')}"