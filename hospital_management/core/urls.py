from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, DoctorViewSet, AppointmentViewSet, MedicalRecordViewSet, VitalSignsViewSet, DiagnosisViewSet, MedicationViewSet, SpecialtyViewSet, ProfileView

router = DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'doctors', DoctorViewSet)
router.register(r'vitals', VitalSignsViewSet)
router.register(r'diagnoses', DiagnosisViewSet)
router.register(r'medications', MedicationViewSet)
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'medical-records', MedicalRecordViewSet)
router.register(r'specialties', SpecialtyViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', ProfileView.as_view(), name='profile'),
]