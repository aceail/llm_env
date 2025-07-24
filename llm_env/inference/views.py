# llm_env/inference/views.py

from django.shortcuts import render, redirect
from django.views import View
import re
import csv
import ast
import openpyxl
import os # os 라이브러리 임포트
import shutil # 파일 복사를 위한 shutil 라이브러리 임포트
from django.conf import settings # Django 설정값을 가져오기 위해 임포트

from .models import InferenceResult
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render, redirect
from django.views import View
import re
import csv
import json
import ast
import openpyxl
import os
import shutil
import uuid
from django.conf import settings
import threading
import logging # 디버깅을 위한 logging 라이브러리 임포트
from django.db.models import Case, When, Value, IntegerField
from .models import InferenceResult
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from pathlib import Path
import sys
from dicom_project_template.LLM_main import main as dicom_llm_main


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # INFO 레벨 이상의 로그를 출력하도록 설정



@method_decorator(login_required, name='dispatch')
class UploadCsvView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'inference/upload_csv.html')

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return render(request, 'inference/upload_csv.html', {'error': '파일을 업로드해주세요.'})

        file_name = uploaded_file.name
        rows = []
        logger.info(f"==================================================")
        logger.info(f"'{file_name}' 파일 업로드 처리를 시작합니다.")

        try:
            if file_name.endswith('.csv'):
                csv_text = uploaded_file.read().decode('utf-8-sig')
                reader = csv.DictReader(csv_text.splitlines())
                rows = list(reader)
            elif file_name.endswith('.xlsx'):
                workbook = openpyxl.load_workbook(uploaded_file)
                sheet = workbook.active
                header = [cell.value for cell in sheet[1]]
                for row_cells in sheet.iter_rows(min_row=2):
                    row_data = {header[i]: cell.value for i, cell in enumerate(row_cells)}
                    rows.append(row_data)
            else:
                return render(request, 'inference/upload_csv.html', {'error': 'CSV 또는 XLSX 파일만 업로드할 수 있습니다.'})

            logger.info(f"파일에서 총 {len(rows)}개의 행(row)을 읽었습니다.")
            
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)

            for i, row in enumerate(rows):
                logger.info(f"--- [ {i+1}번째 행 처리 시작 ] ---")
                logger.info(f"Row Data: {row}")

                try:
                    # ▼▼▼ 솔루션 이름 추출 로직 ▼▼▼
                    solution_name = row.get('JLK-Solution', '') # 'JLK-Solution' 컬럼 값을 가져옵니다.
                    logger.info(f"  [솔루션 이름]: {solution_name if solution_name else '없음'}")
                    # ▲▲▲ 솔루션 이름 추출 로직 ▲▲▲
                    
                    system_prompt = row.get('System Prompt', '')
                    user_prompt = row.get('User Prompt', '')
                    
                    image_urls_str = row.get('Image Path', '[]')
                    logger.info(f"  [Image Path 원본 문자열]: {image_urls_str}")
                    
                    local_image_paths = []
                    if image_urls_str and image_urls_str.strip():
                        try:
                            local_image_paths = ast.literal_eval(image_urls_str)
                        except (ValueError, SyntaxError):
                             logger.error(f"  [오류] Image Path 파싱 실패: {image_urls_str}")
                             local_image_paths = []
                    
                    web_image_urls = []
                    for local_path in local_image_paths:
                        # ... (이미지 처리 로직은 이전과 동일)
                        if local_path and os.path.exists(local_path):
                            original_filename = os.path.basename(local_path)
                            filename_base, file_extension = os.path.splitext(original_filename)
                            unique_filename = f"{filename_base}_{uuid.uuid4().hex[:8]}{file_extension}"
                            destination_path = os.path.join(upload_dir, unique_filename)
                            shutil.copy2(local_path, destination_path)
                            web_url = os.path.join(settings.MEDIA_URL, 'uploads', unique_filename).replace("\\", "/")
                            web_image_urls.append(web_url)
                        else:
                            # ...
                            if local_path:
                                web_image_urls.append(f"NOT_FOUND: {local_path}")
                    
                    llm_output_str = row.get('LLM result', '{}')
                    llm_output = ast.literal_eval(llm_output_str) if llm_output_str and llm_output_str.strip() else {}

                    # ▼▼▼ DB 생성 시 solution_name 필드 추가 ▼▼▼
                    InferenceResult.objects.create(
                        solution_name=solution_name,
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        image_urls=web_image_urls,
                        llm_output=llm_output,
                    )
                    logger.info(f"  DB 저장 완료. 솔루션: {solution_name}, 저장된 URL: {web_image_urls}")

                except Exception as e:
                    logger.error(f"  [오류] 행 처리 중 심각한 오류 발생 (행 번호: {i+2}): {e}", exc_info=True)

            logger.info("모든 행의 처리가 완료되었습니다.")

        except Exception as e:
            logger.error(f"파일 처리 중 예측하지 못한 최상위 오류 발생: {e}", exc_info=True)
            return render(request, 'inference/upload_csv.html', {'error': f'파일 처리 중 예측하지 못한 오류 발생: {e}'})

        return redirect('evaluation')

@method_decorator(login_required, name='dispatch')
class UploadZipView(View):
    """Handle ZIP uploads and run dicom processing"""

    def get(self, request, *args, **kwargs):
        return render(request, 'inference/upload_zip.html')

    def post(self, request, *args, **kwargs):
        uploaded = request.FILES.get('zip_file')
        if not uploaded:
            return render(request, 'inference/upload_zip.html', {'error': '파일을 업로드해주세요.'})

        upload_dir = os.path.join(settings.MEDIA_ROOT, 'zip_uploads')
        os.makedirs(upload_dir, exist_ok=True)
        saved_path = os.path.join(upload_dir, uploaded.name)
        with open(saved_path, 'wb+') as dest:
            for chunk in uploaded.chunks():
                dest.write(chunk)

        # Also keep a copy under MEDIA_ROOT/uploads as requested
        uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        shutil.copy2(saved_path, os.path.join(uploads_dir, uploaded.name))

        def run_inference(path):
            results = []
            if dicom_llm_main:
                try:
                    results = dicom_llm_main(path) or []
                except Exception as e:  # pragma: no cover - runtime safeguard
                    logger.error("LLM_main execution failed: %s", e, exc_info=True)

            extract_dir = Path(path).with_suffix("")
            output_dir = Path(settings.BASE_DIR) / f"{Path(path).stem}_output_images"

            media_output_root = Path(settings.MEDIA_ROOT) / "dicom_outputs"
            os.makedirs(media_output_root, exist_ok=True)
            moved_output_dir = media_output_root / output_dir.name
            if output_dir.exists():
                if moved_output_dir.exists():
                    shutil.rmtree(moved_output_dir, ignore_errors=True)
                shutil.move(str(output_dir), moved_output_dir)

            shutil.rmtree(extract_dir, ignore_errors=True)

            def update_paths(data):
                if isinstance(data, dict):
                    return {k: update_paths(v) for k, v in data.items()}
                if isinstance(data, list):
                    return [update_paths(v) for v in data]
                if isinstance(data, str):
                    return data.replace(str(output_dir), str(moved_output_dir))
                return data

            for item in results:
                try:
                    solution_name = item.get('solution', '')
                    output_raw = item.get('result', {})
                    if isinstance(output_raw, str):
                        try:
                            output = json.loads(output_raw)
                        except json.JSONDecodeError:
                            output = {}
                    else:
                        output = output_raw

                    # Preserve image directory information so the evaluation page
                    # can display generated images.
                    if isinstance(output, dict):
                        if item.get('non_mask_dir'):
                            output['non_mask_dir'] = item.get('non_mask_dir')
                        if item.get('ai_dir'):
                            output['ai_dir'] = item.get('ai_dir')

                    output = update_paths(output)

                    InferenceResult.objects.create(
                        solution_name=solution_name,
                        system_prompt="기존과 동일",
                        user_prompt="기존과 동일",
                        llm_output=output,
                    )
                except Exception as e:
                    logger.error("Failed to save result: %s", e, exc_info=True)

        threading.Thread(target=run_inference, args=(saved_path,)).start()

        return redirect('evaluation')

@method_decorator(login_required, name='dispatch')
class InferenceView(View):
    def get(self, request, *args, **kwargs):
        # GET 요청 시 초기 페이지 렌더링
        context = {
            'system_prompt': "You are a helpful assistant.",
        }
        return render(request, 'inference/inference_form.html', context)

    def post(self, request, *args, **kwargs):
        # POST 요청 처리
        system_prompt = request.POST.get('system_prompt', '')
        
        # 프롬프트 시퀀스 데이터 파싱
        prompts = []
        # 'prompts-0-type', 'prompts-1-type' 같은 키들을 찾음
        prompt_keys = sorted([key for key in request.POST if re.match(r'^prompts-\d+-type$', key)])
        
        for type_key in prompt_keys:
            # 인덱스 (예: '0', '1', ...) 추출
            index = type_key.split('-')[1]
            
            prompt_type = request.POST.get(f'prompts-{index}-type')
            prompt_text = request.POST.get(f'prompts-{index}-text')
            
            # 파일들은 request.FILES에서 가져옴
            # getlist를 사용하여 해당 프롬프트의 모든 파일을 리스트로 받음
            uploaded_files = request.FILES.getlist(f'prompts-{index}-files')
            
            prompts.append({
                'type': prompt_type,
                'text': prompt_text,
                'files': uploaded_files  # UploadedFile 객체 리스트
            })

        # TODO: 여기에 파싱된 prompts 데이터를 사용하여 LLM을 호출하는 로직을 구현합니다.
        # 각 'files' 항목에는 UploadedFile 객체가 들어있으므로, 
        # file.read() 등으로 내용을 읽거나 임시 저장하여 모델에 전달할 수 있습니다.
        
        print("System Prompt:", system_prompt)
        print("Prompt Sequence:", prompts)
        for i, p in enumerate(prompts):
            print(f"  Prompt {i+1} ({p['type']}): {p['text']}")
            for f in p['files']:
                print(f"    - File: {f.name} ({f.size} bytes)")


        # 결과를 보여줄 페이지로 컨텍스트 전달
        context = {
            'system_prompt': system_prompt,
            'submitted_prompts': prompts,
        }
        
        # 여기서는 간단히 동일한 폼을 다시 렌더링합니다.
        return render(request, 'inference/inference_form.html', context)
    

@method_decorator(login_required, name='dispatch')
class EvaluationView(View):
    """
    InferenceResult 목록을 정렬하여 보여주는 뷰
    """
    def get(self, request, *args, **kwargs):
        # 1. 'llm_output' 필드가 비어있는지({} 인지) 여부를 기준으로 새로운 필드 'is_evaluated'를 추가합니다.
        #    - llm_output이 비어있으면 is_evaluated = 0 (평가 안됨)
        #    - llm_output에 내용이 있으면 is_evaluated = 1 (평가 완료)
        results_with_order = InferenceResult.objects.annotate(
            is_evaluated=Case(
                When(llm_output__exact={}, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )

        # 2. 'is_evaluated'를 기준으로 오름차순 (0이 먼저),
        #    'created_at'을 기준으로 내림차순 (최신순) 정렬합니다.
        #    결과적으로 평가 안 된 최신 항목이 맨 위로 오게 됩니다.
        ordered_results = results_with_order.order_by('is_evaluated', '-created_at')

        context = {
            'results': ordered_results
        }
        return render(request, 'inference/evaluation.html', context)
