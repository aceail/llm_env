from django.shortcuts import redirect, render

from .models import InferenceResult


def run_inference(request):
    """Create a sample inference result and redirect to evaluation."""

    result = InferenceResult.objects.create(
        system_prompt="You are a helpful assistant that analyzes medical images.",
        user_prompt="Analyze the attached chest X-ray image and identify any abnormalities.",
        image_urls=["https://i.imgur.com/gGRgWf8.jpeg"],
        llm_output={
            "finding": "Possible signs of pneumonia in the lower right lobe.",
            "location": ["right lower lobe"],
            "confidence": 0.85,
            "recommendation": "Suggest further CT scan for confirmation.",
        },
    )

    return redirect("evaluation_detail", pk=result.pk)


def inference_form(request):
    """Simple page to create an inference result using form inputs."""

    defaults = {
        "system_prompt": "You are a helpful assistant that analyzes medical images.",
        "user_prompt": "Analyze the attached chest X-ray image and identify any abnormalities.",
        "image_urls": ["https://i.imgur.com/gGRgWf8.jpeg"],
    }

    if request.method == "POST":
        system_prompt = request.POST.get("system_prompt", defaults["system_prompt"])
        user_prompt = request.POST.get("user_prompt", "")
        image_urls = [url for url in request.POST.getlist("image_url") if url]
        if not image_urls:
            image_urls = defaults["image_urls"]

        llm_output = {
            "finding": "Possible signs of pneumonia in the lower right lobe.",
            "location": ["right lower lobe"],
            "confidence": 0.85,
            "recommendation": "Suggest further CT scan for confirmation.",
        }

        result = InferenceResult.objects.create(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            image_urls=image_urls,
            llm_output=llm_output,
        )

        return redirect("evaluation_detail", pk=result.pk)

    return render(request, "inference/inference_form.html", defaults)

