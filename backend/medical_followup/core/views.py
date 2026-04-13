from django.shortcuts import render, get_object_or_404
from django.db.models import Max
from django.contrib.auth.decorators import login_required
from .models import Patient, FollowUpRecord

def index(request):
    """首页"""
    # 获取登录用户
    user = request.user
    
    # 获取患者数量
    patient_count = Patient.objects.count()
    
    # 获取随访记录数量
    record_count = FollowUpRecord.objects.count()

    # 获取待随访患者数量
    pending_count = Patient.objects.filter(followup_status=Patient.FOLLOWUP_STATUS_PENDING).count()
    
    # 获取最近的5条随访记录
    recent_records = FollowUpRecord.objects.order_by("-record_date")[:5]
    
    context = {
        "user": user,
        "patient_count": patient_count,
        "record_count": record_count,
        "pending_count": pending_count,
        "recent_records": recent_records
    }
    return render(request, "core/index.html", context)


def patient_list(request):
    """患者列表"""
    # 获取登录用户
    user = request.user
    
    # 获取所有患者
    patients = Patient.objects.annotate(last_follow_up=Max('followuprecord__record_date')).order_by('name')
    
    context = {
        "user": user,
        "patients": patients
    }
    return render(request, "core/patient_list.html", context)


def patient_detail(request, patient_id):
    """患者详情"""
    # 获取登录用户
    user = request.user
    
    # 获取患者信息
    patient = get_object_or_404(Patient, id=patient_id)
    
    # 获取该患者的随访记录
    follow_up_records = FollowUpRecord.objects.filter(patient=patient).order_by("-record_date")
    
    context = {
        "user": user,
        "patient": patient,
        "follow_up_records": follow_up_records
    }
    return render(request, "core/patient_detail.html", context)
