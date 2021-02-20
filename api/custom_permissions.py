import logging
from rest_framework import permissions

logger = logging.getLogger(__name__)


class FavouritesOwnerPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.is_superuser


class HasExtraPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not hasattr(view, "extra_permission"):
            logger.error("VIEW ({}) does not have extra_permission defined".format(view))
            return False
        return user.has_perm(view.extra_permission)
