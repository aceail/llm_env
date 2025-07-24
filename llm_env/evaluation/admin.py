from django.contrib import admin
from .models import Evaluation

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    """Admin configuration for Evaluation model"""
    list_display = (
        "id",
        "inference_result",
        "evaluator",
        "agreement",
        "quality",
        "lesion_vessel",
        "lesion_anatomic",
        "created_at",
    )
    list_filter = (
        "agreement",
        "quality",
        "evaluator",
        "lesion_vessel",
        "lesion_anatomic",
    )
    search_fields = ("inference_result__solution_name", "evaluator__username")


