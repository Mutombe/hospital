# middleware.py
from django.utils import timezone
from .models import AuditLog

class EHRAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        if request.path.startswith('/api/'):
            AuditLog.objects.create(
                user=request.user,
                action=request.method,
                resource=request.path,
                timestamp=timezone.now()
            )
        
        return response