# middleware.py
from django.utils import timezone
from .models import AuditLog
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
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
    
class ProfileCompletionMiddleware(MiddlewareMixin):
    """Redirect users to complete profile if not complete"""
    def process_request(self, request):
        # Skip for admin, static files, and API endpoints
        if (request.path.startswith('/admin/') or 
            request.path.startswith('/static/') or
            request.path.startswith('/api/')):
            return
        
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return
            
        # Skip if profile is complete
        if request.user.profile_complete:
            return
            
        # Skip if already on profile page
        if request.path == reverse('profile'):
            return
            
        # Redirect to profile page
        return redirect('profile')