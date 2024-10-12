# public/views_func/account.py
from django.contrib import auth
from django.shortcuts import render
from django.shortcuts import redirect

def myLogin(request):
    errors = []
    data = ''
    next = request.GET.get('next','/')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        if not request.POST.get('username',''):
            errors.append('Enter a user')
        if not request.POST.get('password',''):
            errors.append('Enter a passwd')
        if not errors:
            user = auth.authenticate(username=username,password=password)
            if user is not None and user.is_active:
                auth.login(request,user)
                return redirect('%s' % next)
            else:
                data = '登陆失败，请核对信息'
    return render(request, 'login.html', {'errors': errors, 'data': data},)

def myLogout(request):
    next = request.GET.get('next','/')
    auth.logout(request)
    return redirect('%s' % next)