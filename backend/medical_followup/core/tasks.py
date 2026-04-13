from celery import shared_task
from django.conf import settings
from django.utils import timezone

from accounts.models import DoctorUser
from core.models import FollowUpRecord, Patient
from survey.agent import run_followup_agent


@shared_task
def schedule_daily_followups():
    today = timezone.localdate()
    patients = Patient.objects.filter(next_follow_up_date=today).exclude(
        followup_status=Patient.FOLLOWUP_STATUS_NO_NEEDED
    )

    for patient in patients:
        run_patient_followup.delay(patient.id)

    return {
        "date": str(today),
        "count": patients.count(),
    }


@shared_task
def run_patient_followup(patient_id):
    patient = Patient.objects.get(id=patient_id)

    history_queryset = FollowUpRecord.objects.filter(patient=patient).order_by("-record_date")[:5]
    history_records = [
        {
            "record_date": item.record_date.strftime("%Y-%m-%d %H:%M:%S"),
            "content": item.content,
            "health_assessment": item.health_assessment,
        }
        for item in history_queryset
    ]

    patient_info = {
        "id": patient.id,
        "name": patient.name,
        "gender": patient.gender,
        "age": patient.age,
        "phone": patient.phone,
    }

    result = run_followup_agent(patient_info=patient_info, history_records=history_records)
    decision = result["decision"]

    doctor = DoctorUser.objects.filter(is_active=True).order_by("id").first()
    if doctor is None:
        raise RuntimeError("未找到可用医生用户，无法写入随访记录。")

    FollowUpRecord.objects.create(
        patient=patient,
        doctor=doctor,
        content=result["dialogue_history"],
        health_assessment=result["survey_json"],
        recommendations=result["rag_advice"],
        next_follow_up=(
            timezone.make_aware(
                timezone.datetime.combine(decision["next_date"], timezone.datetime.min.time())
            )
            if decision["next_date"]
            else None
        ),
        need_further_followup=decision["need_followup"],
        decision_reason=decision["reason"],
        ai_generated=True,
    )

    if decision["need_followup"]:
        patient.next_follow_up_date = decision["next_date"]
        patient.followup_status = Patient.FOLLOWUP_STATUS_PENDING
    else:
        patient.next_follow_up_date = None
        patient.followup_status = Patient.FOLLOWUP_STATUS_NO_NEEDED

    patient.save(update_fields=["next_follow_up_date", "followup_status", "updated_at"])

    return {
        "patient_id": patient.id,
        "need_followup": decision["need_followup"],
        "next_date": str(decision["next_date"]) if decision["next_date"] else None,
    }
