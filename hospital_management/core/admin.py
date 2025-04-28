# core/admin.py
from django.contrib import admin
from .models import User, Patient, Profile, Doctor, Diagnosis, Appointment, MedicalRecord

class AdminUserOverview(admin.ModelAdmin):
    list_display = (
        "role",
        "username",
        "email",
    )
    search_fields = (
        "username",
    )

class AdminDoctorOverview(admin.ModelAdmin):
    list_display = (
        "user",
        "specialty",
        "experience_years",
    )
    search_fields = (
        "specialty",
    )
    ordering = ("specialty",)

class AdminAppointmentOverview(admin.ModelAdmin):
    list_display = (
        "patient",
        "doctor",
        "appointment_date",
        "status",
    )
    search_fields = (
        "status",
    )
    ordering = ("appointment_date",)

class AdminMedicalRecordOverview(admin.ModelAdmin):
    list_display = (
        "patient",
        "doctor",
        "diagnosis",
        "prescription",
        "date",
        "notes"
    )
    search_fields = (
        "diagnosis",
    )
    ordering = ("date",)

class AdminDiagnosisOverview(admin.ModelAdmin):
    list_display = (
        "patient",
        "icd_code",
        "diagnosed_date",
        "description",
    )
    search_fields = (
        "description",
    )
    ordering = ("diagnosed_date",)


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
admin.site.register(Doctor, AdminDoctorOverview)
admin.site.register(Appointment, AdminAppointmentOverview)
admin.site.register(MedicalRecord, AdminMedicalRecordOverview)
admin.site.register(Diagnosis, AdminDiagnosisOverview)