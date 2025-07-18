from django.db import models


class InferenceResult(models.Model):
    """Simple model to store an LLM inference output."""

    system_prompt = models.TextField()
    user_prompt = models.TextField()
    # Allow storing multiple image URLs instead of a single one
    # Keep data simple by using JSON list of URLs
    image_urls = models.JSONField(default=list)
    llm_output = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - simple representation
        return f"Inference #{self.pk}"

