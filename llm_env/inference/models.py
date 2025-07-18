from django.db import models


class InferenceResult(models.Model):
    """Simple model to store an LLM inference output."""

    system_prompt = models.TextField()
    user_prompt = models.TextField(blank=True)
    image_urls = models.JSONField(default=list, blank=True)
    llm_output = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"Inference #{self.pk}"

