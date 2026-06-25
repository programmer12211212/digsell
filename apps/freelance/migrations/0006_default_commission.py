from django.db import migrations


def create_default_commission(apps, schema_editor):
    PlatformCommission = apps.get_model("freelance", "PlatformCommission")
    if not PlatformCommission.objects.exists():
        PlatformCommission.objects.create(name="Default", percentage="10.00", is_active=True)


def reverse_commission(apps, schema_editor):
    PlatformCommission = apps.get_model("freelance", "PlatformCommission")
    PlatformCommission.objects.filter(name="Default").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("freelance", "0005_populate_project_slugs"),
    ]

    operations = [
        migrations.RunPython(create_default_commission, reverse_commission),
    ]
