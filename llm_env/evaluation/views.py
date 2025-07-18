from django.shortcuts import render


def evaluation_view(request):
    """Render a static evaluation page for testing."""
    return render(request, 'evaluation/evaluation.html')
