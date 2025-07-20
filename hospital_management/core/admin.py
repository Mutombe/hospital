# core/admin.py
from django.contrib import admin
from .models import User, Patient, PatientHistory, Profile, Doctor, Diagnosis, Appointment, MedicalRecord, Specialty, VitalSigns, Medication

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

class AdminPatientHistoryOverview(admin.ModelAdmin):
    list_display = (
        "patient",
        "changed_by",
        "change_date",
        "field_name",
    )
    search_fields = (
        "field_name",
    )
    ordering = ("change_date",)

class AdminVitalSignsOverview(admin.ModelAdmin):
    list_display = (
        "patient",
        "temperature",
        "blood_pressure_systolic",
        "heart_rate",
        "recorded_at",
        "recorded_by",
        "respiratory_rate",
    )
    search_fields = (
        "temperature",
    )
    ordering = ("recorded_at",)

class AdminMedicationOverview(admin.ModelAdmin):
    list_display = (
        "patient",
        "prescribed_by",
        "name",
        "dosage",
        "frequency",
        "start_date",
        "end_date",
    )
    search_fields = (
        "name",
    )
    ordering = ("name",)

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
        "user",
        "gender",
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

class DoctorSpecialtyOverview(admin.ModelAdmin):
    list_display = (
        "name",
    )
    search_fields = (
        "name",
    )


admin.site.register(User, AdminUserOverview)
admin.site.register(Profile, AdminProfileOverview)
admin.site.register(Patient, AdminPatientOverview)
admin.site.register(Doctor, AdminDoctorOverview)
admin.site.register(Appointment, AdminAppointmentOverview)
admin.site.register(MedicalRecord, AdminMedicalRecordOverview)
admin.site.register(Diagnosis, AdminDiagnosisOverview)
admin.site.register(Specialty, DoctorSpecialtyOverview)
admin.site.register(VitalSigns, AdminVitalSignsOverview)
admin.site.register(Medication, AdminMedicationOverview)
admin.site.register(PatientHistory, AdminPatientHistoryOverview)