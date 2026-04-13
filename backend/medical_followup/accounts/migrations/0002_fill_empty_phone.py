from django.db import migrations


def fill_empty_phone(apps, schema_editor):
    DoctorUser = apps.get_model("accounts", "DoctorUser")
    users = DoctorUser.objects.filter(phone="")

    for user in users:
        user.phone = f"AUTO{user.id:06d}"
        user.save(update_fields=["phone"])


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(fill_empty_phone, noop_reverse),
    ]
