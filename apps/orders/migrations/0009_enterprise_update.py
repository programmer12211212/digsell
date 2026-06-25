import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_alter_order_status_cart_cartitem'),
        ('videos', '0003_coursecategory_remove_videocomment_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='saved_for_later',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='cartitem',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='videos.video'),
        ),
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together={('cart', 'product')},
        ),
        migrations.AddField(
            model_name='order',
            name='commission_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AlterField(
            model_name='order',
            name='coupon_code',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]
