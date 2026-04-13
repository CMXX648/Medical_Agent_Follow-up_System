from django.contrib import admin
from .models import Patient, FollowUpRecord


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "gender",
        "age",
        "phone",
        "next_follow_up_date",
        "followup_status",
        "contact_method",
        "created_at",
    ]
    search_fields = ["name", "phone"]
    list_filter = ["gender", "followup_status", "contact_method"]

@admin.register(FollowUpRecord)
class FollowUpRecordAdmin(admin.ModelAdmin):
    list_display = [
        "patient",
        "doctor",
        "record_date",
        "next_follow_up",
        "need_further_followup",
        "ai_generated",
    ]
    search_fields = ["patient__name", "doctor__name", "content"]
    list_filter = ["record_date", "doctor", "need_further_followup", "ai_generated"]
    raw_id_fields = ["patient", "doctor"]