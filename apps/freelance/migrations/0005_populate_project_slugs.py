from django.db import migrations
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    FreelanceProject = apps.get_model("freelance", "FreelanceProject")
    for project in FreelanceProject.objects.all():
        if not project.slug:
            base = slugify(project.title) or f"project-{project.pk}"
            slug = base
            counter = 1
            while FreelanceProject.objects.filter(slug=slug).exclude(pk=project.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            project.slug = slug
            project.save(update_fields=["slug"])


def reverse_populate(apps, schema_editor):
    FreelanceProject = apps.get_model("freelance", "FreelanceProject")
    FreelanceProject.objects.update(slug="")


class Migration(migrations.Migration):
    dependencies = [
        ("freelance", "0004_freelanceauditlog_freelancecontract_freelancedispute_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_slugs, reverse_populate),
    ]
