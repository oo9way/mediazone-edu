# Generated by Django 4.2 on 2023-04-19 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_group_cost_subscription_cost'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]