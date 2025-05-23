# Generated by Django 5.2 on 2025-05-03 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_alter_deliveryagent_current_location_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='feedback_comments',
            field=models.TextField(blank=True, help_text='Customer comments about the order', null=True, verbose_name='Feedback Comments'),
        ),
        migrations.AddField(
            model_name='order',
            name='feedback_rating',
            field=models.PositiveSmallIntegerField(blank=True, help_text='Customer rating from 1-5', null=True, verbose_name='Feedback Rating'),
        ),
        migrations.AddField(
            model_name='order',
            name='feedback_submitted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Feedback Submission Time'),
        ),
    ]
