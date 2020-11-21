from rest_framework import permissions


class FavouritesOwnerPermission(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.is_superuser
