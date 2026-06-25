from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Advertisement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, max_length=500)),
                ('image', models.ImageField(blank=True, null=True, upload_to='ads/')),
                ('link_url', models.CharField(blank=True, max_length=500)),
                ('ad_type', models.CharField(choices=[('BANNER', 'Banner'), ('CARD', 'Reklama karta'), ('POPUP', 'Popup')], default='CARD', max_length=20)),
                ('placement', models.CharField(choices=[('HOME', 'Bosh sahifa'), ('MARKETPLACE', 'Marketplace'), ('COURSES', 'Video kurslar'), ('SIDEBAR', 'Yon panel'), ('GLOBAL', 'Barcha sahifalar')], default='GLOBAL', max_length=20)),
                ('bg_color', models.CharField(blank=True, default='#0ea5e9', max_length=20)),
                ('text_color', models.CharField(blank=True, default='#ffffff', max_length=20)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('show_from', models.DateTimeField(blank=True, null=True)),
                ('show_until', models.DateTimeField(blank=True, null=True)),
                ('click_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Reklama',
                'verbose_name_plural': 'Reklamalar',
                'ordering': ['order', '-created_at'],
            },
        ),
    ]
