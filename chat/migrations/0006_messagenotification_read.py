# Generated by Django 4.2.16 on 2024-10-23 09:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_messagenotification'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagenotification',
            name='read',
            field=models.BooleanField(default=False),
        ),
    ]