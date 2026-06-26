from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_wallet_architecture'),
    ]

    operations = [
        migrations.AddField(
            model_name='hamyonpayment',
            name='fee_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
    ]
