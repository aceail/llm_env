# llm_env/inference/views.py

from django.shortcuts import render, redirect # redirect 추가
from django.views import View
import re
import csv  # 추가
import json # 추가
from .models import InferenceResult # 추가


class UploadCsvView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'inference/upload_csv.html')

    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            return render(request, 'inference/upload_csv.html', {'error': '올바른 CSV 파일을 업로드해주세요.'})

        try:
            # UTF-8로 디코딩하여 텍스트를 처리합니다.
            reader = csv.DictReader(csv_file.read().decode('utf-8').splitlines())
            for row in reader:
                # 'Image Path'는 쉼표로 구분된 URL 목록일 수 있으므로 파싱합니다.
                image_urls = [url.strip() for url in row.get('Image Path', '').split(',') if url.strip()]
                
                # 'LLM result'는 JSON 문자열일 가능성이 높으므로 파싱합니다.
                try:
                    llm_output = json.loads(row.get('LLM result', '{}'))
                except json.JSONDecodeError:
                    llm_output = {'error': '잘못된 형식의 LLM result JSON입니다.'}

                InferenceResult.objects.create(
                    system_prompt=row.get('System Prompt', ''),
                    user_prompt=row.get('User Prompt', ''),
                    image_urls=image_urls,
                    llm_output=llm_output,
                )
        except Exception as e:
            return render(request, 'inference/upload_csv.html', {'error': f'파일 처리 중 오류 발생: {e}'})

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