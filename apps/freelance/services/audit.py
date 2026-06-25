from apps.freelance.models import FreelanceAuditLog


def log_audit(user, action: str, model_name: str, object_id, details=None, ip_address=None):
    FreelanceAuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        details=details or {},
        ip_address=ip_address,
    )
