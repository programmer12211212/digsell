from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test

from apps.security.models import AuditLog, SecurityLog
from .permissions import staff_required


@staff_required
def log_center(request):
    tab = request.GET.get('tab', 'audit')
    audit_logs = AuditLog.objects.select_related('admin').order_by('-timestamp')[:100]
    security_logs = SecurityLog.objects.select_related('user').order_by('-timestamp')[:100]
    return render(request, 'adminpanel/logs/center.html', {
        'tab': tab,
        'audit_logs': audit_logs,
        'security_logs': security_logs,
    })