from rest_framework.permissions import IsAuthenticated, BasePermission

class IsPatient(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'PATIENT'

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'DOCTOR'

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'ADMIN'