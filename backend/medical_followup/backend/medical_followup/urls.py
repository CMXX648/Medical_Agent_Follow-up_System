from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
"""
author: cmxx648
"""
urlpatterns = [
    # 后台管理（仅通过直接输入URL访问）
    path('admin/', admin.site.urls),
    
    # 认证相关
    path('accounts/', include('accounts.urls')),
    
    # 核心应用
    path('', include('core.urls')),
]
