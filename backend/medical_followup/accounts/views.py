from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DoctorUser
from django.http import HttpResponseRedirect
from django.urls import reverse


def login_view(request):
    """登录视图"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, '登录成功！')
            return redirect('index')
        else:
            messages.error(request, '用户名或密码错误')
    
    return render(request, 'accounts/login.html')


def register_view(request):
    """注册视图"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')
        department = request.POST.get('department')
        title = request.POST.get('title')
        
        # 验证密码
        if password != confirm_password:
            messages.error(request, '两次输入的密码不一致')
            return redirect('register')
        
        # 检查用户名是否已存在
        if DoctorUser.objects.filter(username=username).exists():
            messages.error(request, '用户名已存在')
            return redirect('register')
        
        # 检查邮箱是否已存在
        if DoctorUser.objects.filter(email=email).exists():
            messages.error(request, '邮箱已存在')
            return redirect('register')
        
        # 检查手机号是否已存在
        if DoctorUser.objects.filter(phone=phone).exists():
            messages.error(request, '手机号已存在')
            return redirect('register')
        
        # 创建用户
        user = DoctorUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            gender=gender,
            phone=phone,
            department=department,
            title=title
        )
        
        # 登录用户
        login(request, user)
        messages.success(request, '注册成功！')
        return redirect('index')
    
    return render(request, 'accounts/register.html')


def logout_view(request):
    """登出视图"""
    logout(request)
    messages.success(request, '已成功登出')
    return redirect('login')


@login_required
def profile_view(request):
    """个人信息视图"""
    user = request.user
    return render(request, 'accounts/profile.html', {'user': user})


@login_required
def edit_profile_view(request):
    """编辑个人信息视图"""
    user = request.user
    
    if request.method == 'POST':
        # 更新基本信息
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.gender = request.POST.get('gender')
        user.phone = request.POST.get('phone')
        user.department = request.POST.get('department')
        user.title = request.POST.get('title')
        user.bio = request.POST.get('bio')
        
        # 保存更新
        user.save()
        messages.success(request, '个人信息已更新')
        return redirect('profile')
    
    return render(request, 'accounts/edit_profile.html', {'user': user})
