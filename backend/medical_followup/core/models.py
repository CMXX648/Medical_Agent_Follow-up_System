from django.db import models
from django.utils import timezone
from django.conf import settings


class Patient(models.Model):
    """患者信息模型"""
    FOLLOWUP_STATUS_PENDING = "pending"
    FOLLOWUP_STATUS_COMPLETED = "completed"
    FOLLOWUP_STATUS_NO_NEEDED = "no_needed"
    FOLLOWUP_STATUS_CHOICES = [
        (FOLLOWUP_STATUS_PENDING, "待随访"),
        (FOLLOWUP_STATUS_COMPLETED, "已完成"),
        (FOLLOWUP_STATUS_NO_NEEDED, "无需继续"),
    ]

    CONTACT_METHOD_PHONE = "phone"
    CONTACT_METHOD_SMS = "sms"
    CONTACT_METHOD_WECHAT = "wechat"
    CONTACT_METHOD_CHOICES = [
        (CONTACT_METHOD_PHONE, "电话"),
        (CONTACT_METHOD_SMS, "短信"),
        (CONTACT_METHOD_WECHAT, "微信"),
    ]

    name = models.CharField(max_length=100, verbose_name="姓名")
    gender = models.CharField(max_length=10, verbose_name="性别")
    age = models.IntegerField(verbose_name="年龄")
    phone = models.CharField(max_length=20, unique=True, verbose_name="电话号码")
    next_follow_up_date = models.DateField(blank=True, null=True, verbose_name="下次随访日期")
    followup_status = models.CharField(
        max_length=20,
        choices=FOLLOWUP_STATUS_CHOICES,
        default=FOLLOWUP_STATUS_PENDING,
        verbose_name="随访状态",
    )
    contact_method = models.CharField(
        max_length=20,
        choices=CONTACT_METHOD_CHOICES,
        default=CONTACT_METHOD_PHONE,
        verbose_name="随访方式",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "患者"
        verbose_name_plural = "患者"
    
    def __str__(self):
        return f"{self.name} - {self.phone}"

class FollowUpRecord(models.Model):
    """随访记录模型"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="患者")
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="医生")
    record_date = models.DateTimeField(default=timezone.now, verbose_name="随访日期")
    content = models.TextField(verbose_name="随访内容")
    health_assessment = models.TextField(blank=True, verbose_name="健康评估")
    recommendations = models.TextField(blank=True, verbose_name="建议措施")
    next_follow_up = models.DateTimeField(blank=True, null=True, verbose_name="下次随访时间")
    need_further_followup = models.BooleanField(default=True, verbose_name="是否需继续跟进")
    decision_reason = models.TextField(blank=True, verbose_name="继续跟进判断理由")
    ai_generated = models.BooleanField(default=False, verbose_name="是否AI自动随访")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "随访记录"
        verbose_name_plural = "随访记录"
        ordering = ["-record_date"]
    
    def __str__(self):
        return f"{self.patient.name} - {self.record_date.strftime('%Y-%m-%d')}"