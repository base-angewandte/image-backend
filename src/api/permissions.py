from rest_framework import permissions


class TosAcceptedPermission(permissions.BasePermission):
    """Only allows full API access if the ToS where accepted."""

    def has_permission(self, request, view):
        if request.user.tos_accepted:
            return True

        # TODO: discuss in review whether this is the best way to check
        #   we could also use an isinstance check on the view, and the action if it is a ViewSet
        #   but this would require some imports and also a way to identified the WrappedAPIView of the get_user_data
        endpoint = request.path.strip().split('/')[-2]
        return endpoint in ['tos', 'user', 'v1']
