import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BonusRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('percentage', models.DecimalField(decimal_places=2, help_text='Xariddan beriladigan bonus foizi', max_digits=5)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('subtitle', models.CharField(blank=True, max_length=300)),
                ('image', models.ImageField(upload_to='banners/')),
                ('link_url', models.CharField(blank=True, max_length=500)),
                ('banner_type', models.CharField(choices=[('WEB', 'Web'), ('MOBILE', 'Mobil'), ('SLIDER', 'Slider')], default='SLIDER', max_length=20)),
                ('order', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='Competition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('comp_type', models.CharField(choices=[('TOP_BUYER', 'Top Xaridor'), ('TOP_SELLER', 'Top Sotuvchi'), ('TOP_REFERRAL', 'Top Referral'), ('TOP_SPENDER', 'Top Spender')], max_length=20)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Promocode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('discount_percent', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('discount_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('valid_from', models.DateTimeField()),
                ('valid_to', models.DateTimeField()),
                ('usage_limit', models.PositiveIntegerField(default=100)),
                ('used_count', models.PositiveIntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='SpinWheelPrize',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('prize_type', models.CharField(choices=[('BONUS', 'Bonus pul'), ('CASHBACK', 'Extra Cashback'), ('PROMO', 'Promokod'), ('FREE_VIDEO', 'Bepul video'), ('NONE', "Yana bir bor urinib ko'ring")], max_length=20)),
                ('value', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('image', models.ImageField(blank=True, null=True, upload_to='marketing/prizes/')),
                ('probability', models.FloatField(help_text='Sovrin chiqish ehtimoli (0-100)')),
            ],
        ),
        migrations.CreateModel(
            name='DailyBonus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('claimed_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Kunlik bonus', 'verbose_name_plural': 'Kunlik bonuslar'},
        ),
        migrations.CreateModel(
            name='Reward',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.PositiveIntegerField()),
                ('title', models.CharField(max_length=100)),
                ('prize_amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('image', models.ImageField(upload_to='marketing/rewards/')),
                ('competition', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rewards', to='marketing.competition')),
            ],
        ),
        migrations.CreateModel(
            name='SpinWheelLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('prize', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='marketing.spinwheelprize')),
            ],
        ),
    ]
