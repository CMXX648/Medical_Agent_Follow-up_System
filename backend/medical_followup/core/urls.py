from django.urls import path
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    # 首页
    path('', login_required(views.index), name='index'),
    # 患者列表
    path('patients/', login_required(views.patient_list), name='patient_list'),
    # 患者详情
    path('patients/<int:patient_id>/', login_required(views.patient_detail), name='patient_detail'),
]
