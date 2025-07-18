from django.shortcuts import redirect

from .models import InferenceResult


def run_inference(request):
    """Create a sample inference result and redirect to evaluation."""

    result = InferenceResult.objects.create(
        system_prompt="You are a helpful assistant that analyzes medical images.",
        user_prompt="Analyze the attached chest X-ray image and identify any abnormalities.",
        image_url="https://i.imgur.com/gGRgWf8.jpeg",
        llm_output={
            "finding": "Possible signs of pneumonia in the lower right lobe.",
            "location": ["right lower lobe"],
            "confidence": 0.85,
            "recommendation": "Suggest further CT scan for confirmation.",
        },
    )

    return redirect("evaluation_detail", pk=result.pk)

