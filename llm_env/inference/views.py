# llm_env/inference/views.py

from django.shortcuts import render, redirect
from django.views import View
import re
import csv
import json
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
import logging # 디버깅을 위한 logging 라이브러리 임포트
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
        logger.info("==================================================")
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

            # enumerate를 사용하여 행 번호를 함께 가져옵니다. (i는 0부터 시작)
            for i, row in enumerate(rows):
                # ▼▼▼ 각 행을 처리하기 전에 로그를 출력합니다. ▼▼▼
                logger.info(f"--- [ {i+1}번째 행 처리 시작 ] ---")
                logger.info(f"Row Data: {row}")

                try:
                    system_prompt = row.get('System Prompt', '')
                    user_prompt = row.get('User Prompt', '')
                    
                    image_urls_str = row.get('Image Path', '[]')
                    logger.info(f"  [Image Path 원본 문자열]: {image_urls_str}")
                    
                    local_image_paths = []
                    # ast.literal_eval은 안전하지만, 문자열이 비어있거나 형식이 잘못되면 오류가 날 수 있습니다.
                    if image_urls_str and image_urls_str.strip():
                        try:
                            local_image_paths = ast.literal_eval(image_urls_str)
                            logger.info(f"  [파싱된 이미지 경로 리스트]: {local_image_paths}")
                        except (ValueError, SyntaxError):
                             logger.error(f"  [오류] Image Path 파싱 실패! 문자열 형식을 확인해주세요: {image_urls_str}")
                             local_image_paths = [] # 파싱 실패 시 빈 리스트로 초기화
                    else:
                        logger.info("  [정보] Image Path가 비어있습니다.")


                    web_image_urls = []
                    
                    for local_path in local_image_paths:
                        logger.info(f"    - 처리할 이미지 경로: '{local_path}'")
                        if local_path and os.path.exists(local_path):
                            original_filename = os.path.basename(local_path)
                            filename_base, file_extension = os.path.splitext(original_filename)
                            unique_filename = f"{filename_base}_{uuid.uuid4().hex[:8]}{file_extension}"
                            
                            destination_path = os.path.join(upload_dir, unique_filename)
                            shutil.copy2(local_path, destination_path)
                            logger.info(f"      [성공] 파일 복사 완료: {destination_path}")
                            
                            web_url = os.path.join(settings.MEDIA_URL, 'uploads', unique_filename).replace("\\", "/")
                            web_image_urls.append(web_url)
                        else:
                            logger.warning(f"      [경고] 파일을 찾을 수 없거나 경로가 비어있습니다: '{local_path}'")
                            if local_path:
                                web_image_urls.append(f"NOT_FOUND: {local_path}")
                    
                    llm_output_str = row.get('LLM result', '{}')
                    llm_output = ast.literal_eval(llm_output_str) if llm_output_str and llm_output_str.strip() else {}

                    InferenceResult.objects.create(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        image_urls=web_image_urls,
                        llm_output=llm_output,
                    )
                    logger.info(f"  DB 저장 완료. 저장된 URL: {web_image_urls}")

                except Exception as e:
                    logger.error(f"  [오류] 행 처리 중 심각한 오류 발생 (행 번호: {i+2}): {e}", exc_info=True)
                    # 오류가 발생해도 다음 행을 계속 처리하도록 'continue'를 사용할 수 있습니다.
                    # 또는 여기서 처리를 중단하고 사용자에게 오류를 알릴 수도 있습니다.
                    # continue 

            logger.info("모든 행의 처리가 완료되었습니다.")

        except Exception as e:
            logger.error(f"파일 처리 중 예측하지 못한 최상위 오류 발생: {e}", exc_info=True)
            return render(request, 'inference/upload_csv.html', {'error': f'파일 처리 중 예측하지 못한 오류 발생: {e}'})

        return redirect('evaluation')
# ... (InferenceView 클래스는 그대로 유지) ...
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