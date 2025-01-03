# Generated by Django 4.2.16 on 2024-12-13 06:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_user_mobile_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='community',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='custom_id',
            field=models.CharField(editable=False, max_length=255, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='family_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='living_in',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='profile_for',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
    ]
