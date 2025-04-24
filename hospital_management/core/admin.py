# core/admin.py
from django.contrib import admin
from .models import User, Patient, Profile

class AdminUserOverview(admin.ModelAdmin):
    list_display = (
        "role",
        "username",
        "email",
    )
    search_fields = (
        "username",
    )

class AdminPatientOverview(admin.ModelAdmin):
    list_display = (
        "mrn",
        "date_of_birth",
        "blood_type",
    )
    search_fields = (
        "blood_type",
    )
    ordering = ("blood_type",)
    list_filter = (
        "blood_type",
    )

class AdminProfileOverview(admin.ModelAdmin):
    list_display = (
        "user",
        "phone_number",
        "address",
        "profile_picture"
    )
    search_fields = (
        "phone_number",
    )


admin.site.register(User, AdminUserOverview)
admin.site.register(Profile, AdminProfileOverview)
admin.site.register(Patient, AdminPatientOverview)