from rest_framework import permissions

from apps.adminpanel.permissions import is_admin_user


class IsProjectClient(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.client_id == request.user.id


class IsProjectFreelancer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return getattr(obj, "assigned_freelancer_id", None) == request.user.id


class IsProposalOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.freelancer_id == request.user.id


class IsFreelanceAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)


def user_can_view_project(user, project):
    if not user.is_authenticated:
        return project.status == project.Status.OPEN
    return user.id in (
        project.client_id,
        project.assigned_freelancer_id,
    ) or project.status == project.Status.OPEN


def user_can_bid(user, project):
    return (
        user.is_authenticated
        and project.client_id != user.id
        and project.status == project.Status.OPEN
    )
