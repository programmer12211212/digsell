import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('videos', '0003_coursecategory_remove_videocomment_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursecategory',
            name='parent',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='children', to='videos.coursecategory',
            ),
        ),
        migrations.AddField(
            model_name='video',
            name='product_type',
            field=models.CharField(
                choices=[
                    ('PHYSICAL', 'Physical Product'),
                    ('DIGITAL', 'Digital File (PDF/ZIP/EXE)'),
                    ('VIDEO', 'Premium Video Course'),
                    ('SERVICE', 'Professional Service'),
                ],
                default='VIDEO', max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='video',
            name='hls_root',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='video',
            name='is_protected',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='videopurchase',
            name='order_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.CreateModel(
            name='DigitalFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='secure_downloads/%Y/%m/')),
                ('version', models.CharField(default='1.0.0', max_length=20)),
                ('is_main', models.BooleanField(default=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='videos.video')),
            ],
        ),
    ]
