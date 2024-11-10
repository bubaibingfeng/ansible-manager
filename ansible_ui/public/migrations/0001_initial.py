# Generated by Django 3.2.20 on 2024-10-24 08:49

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
                ('cluster_name', models.CharField(max_length=80, unique=True)),
                ('master_ip', models.CharField(max_length=80, unique=True)),
                ('node_ip', models.JSONField(max_length=80)),
                ('ntp_server', models.CharField(default='172.20.134.10', max_length=80)),
            ],
        ),
        migrations.CreateModel(
            name='KVM',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vm_name', models.CharField(max_length=80, unique=True)),
                ('vm_ip', models.CharField(max_length=80)),
                ('vm_ssh_user', models.CharField(max_length=80)),
                ('vm_ssh_pass', models.CharField(max_length=80)),
                ('vm_ssh_port', models.CharField(max_length=80)),
                ('vm_ip_reachable', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vm_name', models.CharField(max_length=80, unique=True)),
                ('vm_cpu_usage', models.CharField(default='暂无数据,请10s后重新刷新', max_length=80)),
                ('vm_memory_usage', models.CharField(default='暂无数据', max_length=80)),
                ('vm_disk_usage', models.CharField(default='暂无数据', max_length=80)),
                ('update_time', models.CharField(default='暂无数据', max_length=80)),
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
            name='VM',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vm_name', models.CharField(max_length=80, unique=True)),
                ('kvm_name', models.CharField(max_length=80)),
                ('vm_ip', models.CharField(max_length=80)),
                ('vm_ssh_user', models.CharField(max_length=80)),
                ('vm_ssh_pass', models.CharField(max_length=80)),
                ('vm_ssh_port', models.CharField(max_length=80)),
                ('vm_cpu', models.CharField(max_length=80)),
                ('vm_memory', models.CharField(max_length=80)),
                ('vm_disk', models.CharField(max_length=80)),
                ('vm_ip_reachable', models.BooleanField(default=False)),
                ('vm_useable', models.BooleanField(default=True)),
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
