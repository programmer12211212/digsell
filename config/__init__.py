from django.template import context
from copy import copy

# Patch for Python 3.14 compatibility in Django 5.1 template context copying.
# Django 5.1's Context/RenderContext.__copy__ implementations use super().__copy__(),
# which is incompatible with Python 3.14. These patches preserve state while keeping
# admin/template rendering working.
_original_context_copy = context.Context.__copy__
_original_render_context_copy = context.RenderContext.__copy__

def _patched_context_copy(self):
    duplicate = self.__class__(self.flatten(), autoescape=self.autoescape, use_l10n=self.use_l10n, use_tz=self.use_tz)
    duplicate.render_context = copy(self.render_context)
    duplicate.template = self.template
    duplicate.template_name = self.template_name
    return duplicate

def _patched_render_context_copy(self):
    duplicate = self.__class__()
    duplicate.dicts = self.dicts[:]
    return duplicate

context.Context.__copy__ = _patched_context_copy
context.RenderContext.__copy__ = _patched_render_context_copy

# Initialize Celery app
from .celery import app as celery_app

__all__ = ('celery_app',)
