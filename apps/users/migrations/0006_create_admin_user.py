from django.db import migrations


def create_admin(apps, schema_editor):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    username = 'admin'
    email = 'admin@example.com'
    password = 'admin123'
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_has_saved_card'),
    ]

    operations = [
        migrations.RunPython(create_admin, reverse_code=migrations.RunPython.noop),
    ]
