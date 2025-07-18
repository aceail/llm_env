# llm_env/users/views.py

from django.shortcuts import render, redirect
# UserCreationForm은 더 이상 필요 없으므로 삭제합니다.
from django.contrib.auth import login, authenticate, logout
# AuthenticationForm만 남겨둡니다.
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.urls import reverse
# signup_view 함수 전체를 삭제합니다.

def login_view(request):
    """로그인 뷰"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # ?next= 파라미터가 있으면 그곳으로, 없으면 evaluation 페이지로 이동
                next_url = request.GET.get('next', reverse('evaluation'))
                return redirect(next_url)
    else:
        form = AuthenticationForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """로그아웃 뷰"""
    logout(request)
    return redirect('login')