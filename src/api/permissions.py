from rest_framework import permissions

from django.urls import reverse_lazy


class TosAcceptedPermission(permissions.BasePermission):
    """Only allows full API access if the ToS were accepted."""

    def __init__(self):
        super().__init__()
        versions = ['v1']
        view_names = ['api-root', 'user-list', 'tos-list', 'tos-accept']
        self.allowed_paths = [
            reverse_lazy(view_name, kwargs={'version': version})
            for view_name in view_names
            for version in versions
        ]

    def has_permission(self, request, view):
        if request.user.tos_accepted:
            return True

        return request.path in self.allowed_paths
