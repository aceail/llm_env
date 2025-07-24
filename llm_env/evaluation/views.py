from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test  # 로그인 여부 확인 및 권한 확인
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.conf import settings  # settings 임포트
from django.http import HttpResponse
from inference.models import InferenceResult
from .models import Evaluation  # 방금 만든 Evaluation 모델을 임포트합니다.
from django.db.models import Case, When, Value, IntegerField
import os  # os 임포트
import json
import csv
import io
import zipfile

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
@login_required
def evaluation_list(request):
    first_item = InferenceResult.objects.order_by('-created_at').first()
    if first_item:
        # 첫 번째 아이템의 상세 페이지로 이동
        return redirect('evaluation_detail', pk=first_item.pk)
    
    # 아무 항목도 없을 경우 빈 페이지 렌더링
    return render(request, 'evaluation/evaluation.html')

@login_required
def evaluation_detail(request, pk):
    # ▼▼▼ 정렬 로직 수정 시작 ▼▼▼

    # 1. 현재 사용자가 평가한 모든 항목의 ID를 가져옵니다.
    evaluated_ids = set(Evaluation.objects.filter(
        evaluator=request.user
    ).values_list('inference_result_id', flat=True))

    # 2. 'is_evaluated' 라는 임시 필드를 만들어 정렬에 사용합니다.
    #    - 평가된 항목(ID가 evaluated_ids에 포함)은 is_evaluated = 1
    #    - 평가되지 않은 항목은 is_evaluated = 0
    all_results = InferenceResult.objects.annotate(
        is_evaluated=Case(
            When(pk__in=evaluated_ids, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('is_evaluated', '-created_at') # 평가안됨(0) -> 평가됨(1) 순, 그 다음 최신순으로 정렬

    # ▲▲▲ 정렬 로직 수정 끝 ▲▲▲

    paginator = Paginator(all_results, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    selected_item = get_object_or_404(InferenceResult, pk=pk)

    display_image_urls = []
    if selected_item.image_urls and isinstance(selected_item.image_urls, list):
        for path in selected_item.image_urls:
            # URL인 경우와 로컬 파일 경로인 경우를 모두 처리
            if path.startswith('http://') or path.startswith('https://') or path.startswith('/media/'):
                 display_image_urls.append(path)
            else:
                try:
                    relative_path = os.path.relpath(path, settings.MEDIA_ROOT)
                    display_image_urls.append(os.path.join(settings.MEDIA_URL, relative_path).replace("\\", "/"))
                except ValueError:
                    display_image_urls.append(path)

    # 추가: llm_output 내 디렉토리의 이미지도 표시
    llm_dirs = []
    if isinstance(selected_item.llm_output, dict):
        if 'non_mask_dir' in selected_item.llm_output:
            llm_dirs.append(selected_item.llm_output.get('non_mask_dir'))
        if 'ai_dir' in selected_item.llm_output:
            llm_dirs.append(selected_item.llm_output.get('ai_dir'))

    for img_dir in llm_dirs:
        if not img_dir:
            continue
        if os.path.isdir(img_dir):
            for fname in sorted(os.listdir(img_dir)):
                if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    local_path = os.path.join(img_dir, fname)
                    if local_path.startswith(str(settings.MEDIA_ROOT)):
                        relative_path = os.path.relpath(local_path, settings.MEDIA_ROOT)
                        url = os.path.join(settings.MEDIA_URL, relative_path).replace("\\", "/")
                        display_image_urls.append(url)
                    else:
                        display_image_urls.append(local_path)

    display_image_urls = list(dict.fromkeys(display_image_urls))
    llm_result_formatted = json.dumps(selected_item.llm_output, indent=4, ensure_ascii=False)

    user_evaluation = None
    if request.user.is_authenticated:
        user_evaluation = Evaluation.objects.filter(
            inference_result=selected_item,
            evaluator=request.user
        ).first()

    context = {
        'system_prompt': selected_item.system_prompt,
        'user_prompt': selected_item.user_prompt,
        'selected_id': selected_item.pk,
        'page_obj': page_obj,
        'display_image_urls': display_image_urls,
        'llm_result_formatted': llm_result_formatted,
        'user_evaluation': user_evaluation,
        'evaluated_ids': evaluated_ids,
        # solution_name을 context에 추가합니다.
        'solution_name': selected_item.solution_name
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
    lesion_vessel = request.POST.get('lesion_vessel', '')
    lesion_anatomic = request.POST.get('lesion_anatomic', '')

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
            'lesion_vessel': lesion_vessel,
            'lesion_anatomic': lesion_anatomic,
        }
    )

    # 저장이 끝나면 다시 원래 보던 페이지로 이동
    return redirect('evaluation_detail', pk=pk)


@login_required
@user_passes_test(lambda u: u.is_staff)
def download_paired_results(request):
    """Download all inference results and their evaluations as a zip file.

    Only staff users can access this view so that administrators are able to
    download results produced by every user.
    """
    evaluations = Evaluation.objects.select_related("inference_result", "evaluator")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zip_file:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(
            [
                "evaluation_id",
                "evaluator",
                "inference_id",
                "solution_name",
                "system_prompt",
                "user_prompt",
                "image_urls",
                "llm_output",
                "agreement",
                "quality",
                "comment",
                "lesion_vessel",
                "lesion_anatomic",
                "created_at",
            ]
        )

        for eva in evaluations:
            ir = eva.inference_result
            csv_image_paths = []

            if ir.image_urls:
                for url in ir.image_urls:
                    if url.startswith("http://") or url.startswith("https://"):
                        csv_image_paths.append(url)
                        continue

                    local_path = url
                    if url.startswith(settings.MEDIA_URL):
                        relative = url[len(settings.MEDIA_URL):].lstrip("/")
                        local_path = os.path.join(settings.MEDIA_ROOT, relative)

                    if os.path.exists(local_path):
                        filename = os.path.basename(local_path)
                        arcname = os.path.join("images", filename)
                        zip_file.write(local_path, arcname=arcname)
                        csv_image_paths.append(os.path.join("images", filename))
                    else:
                        csv_image_paths.append(url)

            writer.writerow(
                [
                    eva.id,
                    eva.evaluator.username,
                    ir.id,
                    ir.solution_name,
                    ir.system_prompt,
                    ir.user_prompt,
                    ";".join(csv_image_paths),
                    json.dumps(ir.llm_output, ensure_ascii=False),
                    eva.agreement,
                    eva.quality,
                    eva.comment,
                    eva.lesion_vessel,
                    eva.lesion_anatomic,
                    eva.created_at.isoformat(),
                ]
            )

        zip_file.writestr("evaluations.csv", csv_buffer.getvalue().encode('utf-8-sig'))

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=paired_results.zip"
    return response
