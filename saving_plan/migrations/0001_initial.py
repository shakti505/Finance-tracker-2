# Generated by Django 5.1.3 on 2025-02-11 08:06

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SavingsPlan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=100)),
                ('target_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('original_deadline', models.DateField()),
                ('current_deadline', models.DateField()),
                ('priority', models.CharField(choices=[('HIGH', 'High'), ('MEDIUM', 'Medium'), ('LOW', 'Low')], max_length=10)),
                ('frequency', models.CharField(choices=[('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly')], max_length=10)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('COMPLETED', 'Completed'), ('EXTENDED', 'Extended'), ('FAILED', 'Failed')], default='ACTIVE', max_length=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='savings_plans', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DeadlineExtension',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('previous_deadline', models.DateField()),
                ('new_deadline', models.DateField()),
                ('reason', models.TextField(blank=True)),
                ('extended_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deadline_extensions', to=settings.AUTH_USER_MODEL)),
                ('savings_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deadline_extensions', to='saving_plan.savingsplan')),
            ],
            options={
                'ordering': ['-extended_at'],
            },
        ),
        migrations.CreateModel(
            name='SavingsTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True)),
                ('savings_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='saving_plan.savingsplan')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='savings_transactions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date'],
            },
        ),
        migrations.AddConstraint(
            model_name='savingsplan',
            constraint=models.CheckConstraint(condition=models.Q(('target_amount__gt', 0)), name='positive_target_amount'),
        ),
    ]
