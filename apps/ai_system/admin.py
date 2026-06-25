from django.contrib import admin
from .models import AIInteraction, AIConfig

@admin.register(AIInteraction)
class AIInteractionAdmin(admin.ModelAdmin):
    list_display = ('interaction_type', 'user', 'tokens_used', 'cost', 'created_at')
    list_filter = ('interaction_type', 'status')
    readonly_fields = ('prompt', 'response', 'created_at')

@admin.register(AIConfig)
class AIConfigAdmin(admin.ModelAdmin):
    list_display = ('key', 'description')
