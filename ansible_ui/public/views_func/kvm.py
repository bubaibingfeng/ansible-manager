from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
import json, datetime, redis, os, random, string, ast
from myCelery import ansiblePlayBook, syncAnsibleResult
from tools.config import REDIS_ADDR, REDIS_PORT, REDIS_PD, ansible_result_redis_db
from public.models import *
from public.admin import writeini

def kvm_list(request):
    kvms = KVM.objects.all()
    return render(request, 'kvm/kvm_list.html', {'kvms': kvms})

def kvm_detail(request, pk):
    kvm = get_object_or_404(KVM, pk=pk)
    if request.method == 'POST':
        form = KVMForm(request.POST, instance=kvm)
        if form.is_valid():
            form.save()
            return redirect('kvm_list')
    else:
        form = KVMForm(instance=kvm)
    return render(request, 'kvm/kvm_detail.html', {'form': form, 'kvm': kvm})

def kvm_create(request):
    if request.method == 'POST':
        form = KVMForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('kvm_list')
    else:
        form = KVMForm()
    return render(request, 'kvm/kvm_form.html', {'form': form})