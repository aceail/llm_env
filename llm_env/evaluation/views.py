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
from .models import Evaluation # 방금 만든 Evaluation 모델을 임포트합니다.
from django.contrib.auth.decorators import login_required # 로그인 여부 확인

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

    display_image_urls = []
    if selected_item.image_urls and isinstance(selected_item.image_urls, list):
        for path in selected_item.image_urls:
            try:
                relative_path = os.path.relpath(path, settings.MEDIA_ROOT)
                display_image_urls.append(os.path.join(settings.MEDIA_URL, relative_path).replace("\\", "/"))
            except ValueError:
                display_image_urls.append(path)

    llm_result_formatted = json.dumps(selected_item.llm_output, indent=4, ensure_ascii=False)

    user_evaluation = None
    evaluated_ids = set() # 빈 세트 생성

    if request.user.is_authenticated:
        # 현재 사용자의 평가 기록 가져오기
        user_evaluation = Evaluation.objects.filter(
            inference_result=selected_item,
            evaluator=request.user
        ).first()
        
        # ▼▼▼ 현재 사용자가 평가한 모든 항목의 ID를 가져옵니다. ▼▼▼
        evaluated_ids = set(Evaluation.objects.filter(
            evaluator=request.user
        ).values_list('inference_result_id', flat=True))
        # ▲▲▲ 코드 추가 ▲▲▲

    context = {
        'system_prompt': selected_item.system_prompt,
        'user_prompt': selected_item.user_prompt,
        'selected_id': selected_item.pk,
        'page_obj': page_obj,
        'display_image_urls': display_image_urls,
        'llm_result_formatted': llm_result_formatted,
        'user_evaluation': user_evaluation,
        'evaluated_ids': evaluated_ids,  # 평가 완료 ID 목록을 템플릿으로 전달
    }
    return render(request, 'evaluation/evaluation.html', context)


@require_POST # POST 요청만 허용하여 안전하게 처리
def delete_all_inferences(request):
    """
    모든 InferenceResult 객체를 삭제합니다.
    """
    InferenceResult.objects.all().delete()
    return redirect('evaluation') # 삭제 후 평가 목록 메인 페이지로 이동


@login_required # 로그인이 필요한 기능
@require_POST   # POST 요청만 허용 (보안)
def submit_evaluation(request, pk):
    inference_result = get_object_or_404(InferenceResult, pk=pk)

    # 템플릿의 form에서 넘어온 데이터 받기
    agreement = request.POST.get('agreement')
    quality = request.POST.get('quality')
    comment = request.POST.get('comment', '') # 코멘트는 없을 수도 있음

    # 필수 값들이 있는지 확인
    if not agreement or not quality:
        # 값이 없으면, 그냥 원래 페이지로 돌아감 (추후 에러 메시지 추가 가능)
        return redirect('evaluation_detail', pk=pk)

    # 동일한 사용자가 동일한 항목에 대해 중복 평가하는 것을 방지
    Evaluation.objects.update_or_create(
        inference_result=inference_result,
        evaluator=request.user,
        defaults={
            'agreement': agreement,
            'quality': int(quality),
            'comment': comment,
        }
    )

    # 저장이 끝나면 다시 원래 보던 페이지로 이동
    return redirect('evaluation_detail', pk=pk)