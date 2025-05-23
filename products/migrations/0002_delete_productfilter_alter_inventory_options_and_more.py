# Generated by Django 5.2 on 2025-05-07 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='ProductFilter',
        ),
        migrations.AlterModelOptions(
            name='inventory',
            options={'verbose_name_plural': 'Inventory'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='productcategory',
            options={'ordering': ['name'], 'verbose_name': 'Product Category', 'verbose_name_plural': 'Product Categories'},
        ),
        migrations.AlterModelOptions(
            name='productimage',
            options={'ordering': ['order']},
        ),
        migrations.AlterModelOptions(
            name='productreview',
            options={'ordering': ['-created_at'], 'verbose_name': 'Product Review', 'verbose_name_plural': 'Product Reviews'},
        ),
        migrations.AlterModelOptions(
            name='relatedproduct',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='stockupdate',
            options={'ordering': ['-timestamp']},
        ),
        migrations.AddField(
            model_name='inventory',
            name='sku',
            field=models.CharField(blank=True, max_length=50, unique=True),
        ),
        migrations.AddField(
            model_name='productcategory',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='productcategory',
            name='featured',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='productimage',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='stockupdate',
            name='note',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='warranty',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
