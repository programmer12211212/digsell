from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST

from apps.security.models import BlockedIP, SecurityLog, AuditLog
from .permissions import staff_required


@staff_required
def security_center(request):
    blocked_ips = BlockedIP.objects.all()[:20]
    security_logs = SecurityLog.objects.select_related('user')[:30]
    audit_logs = AuditLog.objects.select_related('admin')[:30]
    return render(request, 'adminpanel/security/center.html', {
        'blocked_ips': blocked_ips,
        'security_logs': security_logs,
        'audit_logs': audit_logs,
        'critical_count': SecurityLog.objects.filter(level='CRITICAL').count(),
    })


@require_POST
@staff_required
def block_ip(request):
    ip = request.POST.get('ip_address', '').strip()
    reason = request.POST.get('reason', 'Admin tomonidan bloklandi')
    if ip:
        BlockedIP.objects.get_or_create(ip_address=ip, defaults={'reason': reason})
        SecurityLog.objects.create(level='WARNING', action='IP_BLOCKED', ip_address=ip, user=request.user, details={'reason': reason})
        messages.success(request, f'{ip} bloklandi.')
    return redirect('adminpanel:security')


@require_POST
@staff_required
def unblock_ip(request, ip_id):
    ip = get_object_or_404(BlockedIP, id=ip_id)
    ip.delete()
    messages.info(request, 'IP blokdan olindi.')
    return redirect('adminpanel:security')