# Generated by Django 4.2.19 on 2025-02-23 19:00

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='menu',
            options={'permissions': [('can_assign_menu', 'Can assign menu to groups')]},
        ),
        migrations.AddField(
            model_name='menu',
            name='level',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='menu',
            name='lft',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='menu',
            name='rght',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='menu',
            name='tree_id',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='menu',
            name='parent',
            field=mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='menu.menu'),
        ),
    ]
