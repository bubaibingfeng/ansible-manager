# public/views_func/account.py
from django.contrib import auth
from django.shortcuts import render
from django.shortcuts import redirect

import json
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import auth

def myLogin(request):
    errors = []
    data = ''
    next_url = request.GET.get('next', '/')
    
    if request.method == 'POST':
        # Check if the request contains JSON data
        if request.content_type == 'application/json':
            try:
                json_data = json.loads(request.body)
                username = json_data.get('username', '')
                password = json_data.get('password', '')
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON format'
                }, status=400)
        else:
            # Handle traditional form data
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
        
        # Validate input
        if not username:
            errors.append('Enter a user')
        if not password:
            errors.append('Enter a passwd')
            
        if not errors:
            user = auth.authenticate(username=username, password=password)
            if user is not None and user.is_active:
                auth.login(request, user)
                
                # Return response based on request type
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'status': 'success',
                        'redirect_url': next_url
                    })
                return redirect(next_url)
            else:
                data = '登录失败，请核对信息'  # Login failed, please verify information
                
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'status': 'error',
                        'message': data
                    }, status=401)
        
        # Handle validation errors
        if request.content_type == 'application/json':
            return JsonResponse({
                'status': 'error',
                'errors': errors
            }, status=400)
    
    # For non-JSON requests, you might want to render a template
    context = {
        'errors': errors,
        'data': data,
        'next': next_url
    }
    # Return your template here
    return render(request, 'your_login_template.html', context)

def myLogout(request):
    next = request.GET.get('next','/')
    auth.logout(request)
    return redirect('%s' % next)