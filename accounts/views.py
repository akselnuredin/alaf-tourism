from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json


def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect('/admin/')

    if request.method == 'POST':
        # AJAX request handling
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            username = request.POST.get('username')
            password = request.POST.get('password')
            remember = request.POST.get('remember') == 'on'

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)

                # Set session expiry
                if not remember:
                    request.session.set_expiry(0)  # Browser close
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                return JsonResponse({
                    'success': True,
                    'message': 'Login successful!',
                    'redirect_url': '/admin/'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid username or password'
                })

        # Regular form submission
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/admin/')

    return render(request, 'login.html')


def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')
