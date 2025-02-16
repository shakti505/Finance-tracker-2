# Generated by Django 5.1.3 on 2025-02-16 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('saving_plan', '0006_remove_savingsplan_is_completed_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='savingsplan',
            name='status',
            field=models.CharField(choices=[('ACTIVE', 'Active'), ('PAUSED', 'Paused'), ('COMPLETED', 'Completed')], default='ACTIVE', max_length=10),
        ),
    ]
