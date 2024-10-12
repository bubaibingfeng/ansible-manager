# Generated by Django 3.0.1 on 2024-09-24 06:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AnsiblePlaybooks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nickName', models.CharField(blank=True, max_length=80, null=True)),
                ('playbook', models.CharField(max_length=80, null=True, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cluster',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('master_ip', models.CharField(max_length=80, unique=True)),
                ('node_ip', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='Hosts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hostname', models.CharField(blank=True, max_length=80, null=True)),
                ('hostip', models.CharField(max_length=80, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Vars',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('varName', models.CharField(max_length=80, unique=True)),
                ('ssh_pass', models.CharField(max_length=80)),
                ('ssh_port', models.CharField(max_length=80)),
                ('ssh_user', models.CharField(max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='Groups',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('groupName', models.CharField(max_length=80, unique=True)),
                ('hostList', models.ManyToManyField(to='public.Hosts')),
            ],
        ),
        migrations.CreateModel(
            name='AnsibleTasks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('AnsibleID', models.CharField(blank=True, max_length=80, null=True, unique=True)),
                ('CeleryID', models.CharField(blank=True, max_length=80, null=True, unique=True)),
                ('GroupName', models.CharField(blank=True, max_length=80, null=True)),
                ('playbook', models.CharField(blank=True, max_length=80, null=True)),
                ('ExtraVars', models.TextField(blank=True, null=True)),
                ('AnsibleResult', models.TextField(blank=True)),
                ('CeleryResult', models.TextField(blank=True)),
                ('CreateTime', models.DateTimeField(auto_now_add=True, null=True)),
                ('TaskUser', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': '任务列表',
                'verbose_name_plural': '任务列表',
                'ordering': ['id'],
            },
        ),
    ]
