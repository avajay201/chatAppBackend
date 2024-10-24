# Generated by Django 4.2.16 on 2024-10-23 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_report'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='reason',
            field=models.CharField(choices=[('spam', 'Spam'), ('harassment', 'Harassment'), ('offensive', 'Offensive Content')], max_length=50),
        ),
    ]