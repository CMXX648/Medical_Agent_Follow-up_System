from django.urls import path
from . import views

urlpatterns = [
    # 登录
    path('login/', views.login_view, name='login'),
    # 注册
    path('register/', views.register_view, name='register'),
    # 登出
    path('logout/', views.logout_view, name='logout'),
    # 个人信息
    path('profile/', views.profile_view, name='profile'),
    # 编辑个人信息
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
]
