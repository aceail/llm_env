# llm_env/inference/views.py

from django.shortcuts import render, redirect
from django.views import View
import re
import csv
import json
import ast  # ast 라이브러리를 추가합니다.
from .models import InferenceResult
import openpyxl  # openpyxl 라이브러리를 임포트합니다.

class UploadCsvView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'inference/upload_csv.html')

    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return render(request, 'inference/upload_csv.html', {'error': '파일을 업로드해주세요.'})

        file_name = uploaded_file.name
        rows = []  # 파일 데이터를 저장할 리스트

        try:
            # 파일 확장자에 따라 다르게 처리
            if file_name.endswith('.csv'):
                # CSV 파일 처리
                csv_text = uploaded_file.read().decode('utf-8-sig')
                reader = csv.DictReader(csv_text.splitlines())
                rows = list(reader)
            elif file_name.endswith('.xlsx'):
                # XLSX 파일 처리
                workbook = openpyxl.load_workbook(uploaded_file)
                sheet = workbook.active
                
                header = [cell.value for cell in sheet[1]] # 첫 번째 행을 헤더로 사용
                for row_cells in sheet.iter_rows(min_row=2): # 두 번째 행부터 데이터로 읽음
                    row_data = {header[i]: cell.value for i, cell in enumerate(row_cells)}
                    rows.append(row_data)
            else:
                return render(request, 'inference/upload_csv.html', {'error': 'CSV 또는 XLSX 파일만 업로드할 수 있습니다.'})

            # 공통 데이터 처리 로직
            for i, row in enumerate(rows):
                try:
                    system_prompt = row.get('System Prompt', '')
                    user_prompt = row.get('User Prompt', '')
                    
                    # 데이터가 None일 경우를 대비하여 처리
                    image_urls_str = row.get('Image Path', '[]')
                    image_urls = ast.literal_eval(image_urls_str) if image_urls_str else []

                    llm_output_str = row.get('LLM result', '{}')
                    llm_output = ast.literal_eval(llm_output_str) if llm_output_str else {}

                    InferenceResult.objects.create(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        image_urls=image_urls,
                        llm_output=llm_output,
                    )
                except (ValueError, SyntaxError) as e:
                    error_context = {
                        'error': '데이터 파싱 중 오류가 발생했습니다.',
                        'row_number': i + 2, # 헤더 포함 2번째 줄부터 시작
                        'error_details': str(e),
                        'problematic_data': row,
                    }
                    return render(request, 'inference/upload_csv.html', error_context)

        except Exception as e:
            return render(request, 'inference/upload_csv.html', {'error': f'파일 처리 중 예측하지 못한 오류 발생: {e}'})

        return redirect('evaluation')


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