from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required # 추가
from inference.models import InferenceResult
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator # Paginator 임포트
from django.shortcuts import render, get_object_or_404, redirect
from inference.models import InferenceResult
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.conf import settings # settings 임포트
import os # os 임포트
import json

@login_required # 추가
def evaluation_view(request, pk=None):
    """Render the evaluation page using the latest inference result."""

    result = None
    if pk is not None:
        result = get_object_or_404(InferenceResult, pk=pk)
    else:
        result = InferenceResult.objects.order_by('-created_at').first()

    inference_list = InferenceResult.objects.order_by('-created_at')[:10]

    context = {
        'system_prompt': (
            result.system_prompt
            if result
            else 'You are a helpful assistant that analyzes medical images.'
        ),
        'user_prompt': (
            result.user_prompt
            if result
            else 'Analyze the attached chest X-ray image and identify any abnormalities.'
        ),
        'image_urls': (
            result.image_urls
            if result
            else ['https://i.imgur.com/gGRgWf8.jpeg']
        ),
        'llm_result': (
            result.llm_output
            if result
            else {
                'finding': 'Possible signs of pneumonia in the lower right lobe.',
                'location': ['right lower lobe'],
                'confidence': 0.85,
                'recommendation': 'Suggest further CT scan for confirmation.',
            }
        ),
        'inference_list': inference_list,
        'selected_id': result.pk if result else None,
    }

    return render(request, 'evaluation/evaluation.html', context)
@require_POST
def delete_inference(request, pk):
    inference_item = get_object_or_404(InferenceResult, pk=pk)
    inference_item.delete()
    return redirect('evaluation')

def evaluation_list(request):
    first_item = InferenceResult.objects.order_by('-created_at').first()
    if first_item:
        # 첫 번째 아이템의 상세 페이지로 이동
        return redirect('evaluation_detail', pk=first_item.pk)
    
    # 아무 항목도 없을 경우 빈 페이지 렌더링
    return render(request, 'evaluation/evaluation.html')

def evaluation_detail(request, pk):
    all_results = InferenceResult.objects.order_by('-created_at')
    paginator = Paginator(all_results, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    selected_item = get_object_or_404(InferenceResult, pk=pk)

    # 이미지 경로를 웹 URL로 변환
    display_image_urls = []
    if selected_item.image_urls and isinstance(selected_item.image_urls, list):
        for path in selected_item.image_urls:
            # MEDIA_ROOT를 기준으로 상대 경로를 계산하여 URL 생성
            try:
                relative_path = os.path.relpath(path, settings.MEDIA_ROOT)
                display_image_urls.append(os.path.join(settings.MEDIA_URL, relative_path).replace("\\", "/"))
            except ValueError:
                # 경로 계산이 어려운 경우(예: 다른 드라이브), 경로를 그대로 사용
                display_image_urls.append(path)

    # ▼▼▼ LLM Result 처리 로직 추가 ▼▼▼
    # 딕셔너리 형태의 llm_output을 보기 좋게 정렬된 JSON 문자열로 변환합니다.
    llm_result_formatted = json.dumps(selected_item.llm_output, indent=4, ensure_ascii=False)
    # ▲▲▲ LLM Result 처리 로직 추가 ▲▲▲

    context = {
        'system_prompt': selected_item.system_prompt,
        'user_prompt': selected_item.user_prompt,
        'selected_id': selected_item.pk,
        'page_obj': page_obj,
        'display_image_urls': display_image_urls,
        'llm_result_formatted': llm_result_formatted, # 변환된 결과를 context에 추가
    }
    # llm_result는 제거하고, llm_result_formatted를 사용합니다.
    return render(request, 'evaluation/evaluation.html', context)



@require_POST # POST 요청만 허용하여 안전하게 처리
def delete_all_inferences(request):
    """
    모든 InferenceResult 객체를 삭제합니다.
    """
    InferenceResult.objects.all().delete()
    return redirect('evaluation') # 삭제 후 평가 목록 메인 페이지로 이동