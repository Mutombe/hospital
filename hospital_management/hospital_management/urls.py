from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenBlacklistView
from core.views import VerifyEmailView, LoginView, RegisterView, LogoutView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include('core.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('api/verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('api/verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify_email'),
    path('api/verify-email/<uidb64>/<token>/', VerifyEmailView.as_view(), name='verify_email_confirm'),
]
