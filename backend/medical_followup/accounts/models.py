from django.db import models
from django.contrib.auth.models import AbstractUser


class DoctorUser(AbstractUser):
    """医生用户模型"""
    REQUIRED_FIELDS = ["email", "phone", "gender"]

    # 基本信息
    gender = models.CharField(max_length=10, verbose_name="性别")
    phone = models.CharField(max_length=20, unique=True, verbose_name="电话号码")
    department = models.CharField(max_length=100, blank=True, verbose_name="科室")
    title = models.CharField(max_length=100, blank=True, verbose_name="职称")
    
    # 扩展字段
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="头像")
    bio = models.TextField(blank=True, verbose_name="个人简介")
    
    # 登录相关
    email = models.EmailField(unique=True, verbose_name="邮箱")
    
    # 继承AbstractUser的字段：
    # username, password, first_name, last_name, is_staff, is_active, is_superuser
    
    class Meta:
        verbose_name = "医生用户"
        verbose_name_plural = "医生用户"
    
    def __str__(self):
        return f"{self.username} - {self.department}"
