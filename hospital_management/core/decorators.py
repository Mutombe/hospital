from functools import wraps
from rest_framework.exceptions import PermissionDenied

def doctor_required(view_func):
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        if request.user.role != 'DOCTOR':
            raise PermissionDenied("Only doctors can access this endpoint.")
        return view_func(self, request, *args, **kwargs)
    return wrapped_view

def patient_required(view_func):
    @wraps(view_func)
    def wrapped_view(self, request, *args, **kwargs):
        if request.user.role != 'PATIENT':
            raise PermissionDenied("Only patients can access this endpoint.")
        return view_func(self, request, *args, **kwargs)
    return wrapped_view