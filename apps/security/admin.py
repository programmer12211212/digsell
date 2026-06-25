from django.contrib import admin
from .models import BlockedIP, SecurityLog, AuditLog

@admin.register(BlockedIP)
class BlockedIPAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'created_at')
    search_fields = ('ip_address',)

@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('level', 'action', 'ip_address', 'user', 'timestamp')
    list_filter = ('level', 'action')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('admin', 'action', 'model_name', 'timestamp')
    readonly_fields = ('admin', 'action', 'model_name', 'object_id', 'changes', 'timestamp')
