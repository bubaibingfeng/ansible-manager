# Generated by Django 3.0.1 on 2024-10-10 04:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('public', '0004_kvm_kvm_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='kvm',
            name='kvm_name',
        ),
        migrations.AddField(
            model_name='vm',
            name='kvm_name',
            field=models.CharField(default=1, max_length=80),
            preserve_default=False,
        ),
    ]