from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import DoctorUser


class DoctorUserAdmin(UserAdmin):
    """医生用户管理"""
    # 列表显示的字段
    list_display = ('username', 'email', 'phone', 'department', 'title', 'is_staff', 'is_active')
    
    # 搜索字段
    search_fields = ('username', 'email', 'phone', 'department')
    
    # 筛选字段
    list_filter = ('department', 'is_staff', 'is_active')
    
    # 编辑页面的字段布局
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email', 'phone', 'gender', 'department', 'title', 'avatar', 'bio')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('日期', {'fields': ('last_login', 'date_joined')}),
    )

    # 新增页面字段布局（默认UserAdmin不会包含自定义字段）
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'gender', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )


admin.site.register(DoctorUser, DoctorUserAdmin)
