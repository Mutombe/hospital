from rest_framework import viewsets, status
from .models import Patient, Doctor, Appointment, MedicalRecord, User, Diagnosis, VitalSigns, Medication, Specialty, Profile, DoctorLeave, DoctorSchedule
from .serializers import PatientSerializer,ProfileSerializer, DoctorSerializer, SpecialtySerializer, AppointmentSerializer, MedicalRecordSerializer, UserSerializer, CustomTokenObtainPairSerializer, MedicationSerializer, DiagnosisSerializer, VitalSignsSerializer
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django_filters import rest_framework as filters
from .tasks import send_appointment_confirmation
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework.views import APIView
import logging
from rest_framework import status
from .tasks import send_appointment_status_update, send_appointment_notification
from datetime import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            
            # Explicitly validate credentials
            if not serializer.is_valid():
                # Extract specific error messages
                errors = {}
                if 'non_field_errors' in serializer.errors:
                    errors['detail'] = serializer.errors['non_field_errors'][0]
                else:
                    for field, error_list in serializer.errors.items():
                        errors[field] = error_list[0]
                
                return Response(
                    {"errors": errors}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
            response_data = serializer.validated_data
            return Response(response_data, status=status.HTTP_200_OK)
            
        except AuthenticationFailed as e:
            return Response(
                {"errors": {"detail": str(e)}}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"errors": {"detail": "An unexpected error occurred"}}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny] 
    
    def post(self, request):
        user_serializer = UserSerializer(data=request.data)
        if user_serializer.is_valid():
            user = user_serializer.save()
            
            # Create corresponding profile based on role
            if user.role == 'PATIENT':
                Patient.objects.create(
                    user=user,
                    # Add other required fields from request.data
                )
            elif user.role == 'DOCTOR':
                Doctor.objects.create(
                    user=user,
                    # Add other required fields from request.data
                )
                
            # Generate verification token and send email
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_link = f'http://localhost:5173/verify-email/{uid}/{token}/'
            
            subject = "Verify Your Email"
            html_message = render_to_string(
            "verify_email.html",
                {
                    "user": user,
                    "verification_link": verification_link,
                },
            )
            plain_message = strip_tags(html_message)  
            email = EmailMultiAlternatives(
                subject, 
                plain_message, 
                "noreply@healthhub.com", 
                [user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            return Response({
                'message': 'Registration successful. Please verify your email.',
                'user_id': user.id,
                'role': user.role
            }, status=status.HTTP_201_CREATED)
        errors = {}
        for field, error_list in user_serializer.errors.items():
            errors[field] = error_list[0] if isinstance(error_list, list) else error_list
            
        return Response(
            {"errors": errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )

class VerifyEmailView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            if default_token_generator.check_token(user, token):
                user.email_verified = True
                user.is_active = True
                user.save()
                
                # Generate authentication tokens
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user_id': user.id,
                    'role': user.role
                }, status=status.HTTP_200_OK)
            
            return Response(
                {'error': 'Invalid token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'error': 'Invalid verification link'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('mrn', 'gender', 'blood_type')

    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        patient = self.get_object()
        vitals = VitalSigns.objects.filter(patient=patient)
        diagnoses = Diagnosis.objects.filter(patient=patient)
        medications = Medication.objects.filter(patient=patient)

        return Response({
            'vitals': VitalSignsSerializer(vitals, many=True).data,
            'diagnoses': DiagnosisSerializer(diagnoses, many=True).data,
            'medications': MedicationSerializer(medications, many=True).data
        })

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        doctor = self.get_object()
        date_str = request.query_params.get('date')
        
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # For demo purposes, generate time slots from 9 AM to 5 PM
        # without checking doctor's schedule or availability
        available_slots = []
        current_time = datetime.strptime('09:00', '%H:%M').time()
        end_time = datetime.strptime('17:00', '%H:%M').time()
        
        while current_time < end_time:
            available_slots.append(current_time.strftime('%H:%M'))
            # Move to next slot (30 minutes)
            current_time = (datetime.combine(date, current_time) + timedelta(minutes=30)).time()
        
        return Response({
            "available_slots": available_slots,
            "demo_note": "For demo purposes, all times from 9 AM to 5 PM are available"
        })

class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        print(f"User: {user}, Has doctor: {hasattr(user, 'doctor')}, Has patient: {hasattr(user, 'patient')}")
    
        if hasattr(user, 'doctor'):
            queryset = Appointment.objects.filter(doctor__user=user)
            print(f"Doctor appointments: {queryset.count()}")
            return queryset
        elif hasattr(user, 'patient'):
            queryset = Appointment.objects.filter(patient__user=user)
            print(f"Patient appointments: {queryset.count()}")
            return queryset
    
        print("No doctor or patient profile found")
        return Appointment.objects.none()
    def create(self, request, *args, **kwargs):
        try:
            # Create serializer with request context
            serializer = self.get_serializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            
            # Perform creation
            self.perform_create(serializer)
            
            # Send confirmation email
            send_appointment_confirmation.delay(serializer.instance.id)
            
            # Send notification to the doctor
            send_appointment_notification.delay(serializer.instance.id)
            
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            # Log the error for debugging
            import traceback
            print(f"Error creating appointment: {str(e)}")
            print(traceback.format_exc())
            
            return Response(
                {"error": "Failed to create appointment. Please try again."},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        # This will be handled by the serializer's create method
        serializer.save()

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        try:
            appointment = self.get_object()
            
            # Check if the current user is the doctor for this appointment
            if not hasattr(request.user, 'doctor') or appointment.doctor.user != request.user:
                return Response(
                    {"error": "You can only accept your own appointments"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            appointment.status = 'CONFIRMED'
            appointment.save()
            
            # Send confirmation to patient
            send_appointment_status_update.delay(appointment.id, "accepted")
            
            return Response({"status": "Appointment accepted"})
            
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        try:
            appointment = self.get_object()
            
            # Check if the current user is the doctor for this appointment
            if not hasattr(request.user, 'doctor') or appointment.doctor.user != request.user:
                return Response(
                    {"error": "You can only reject your own appointments"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            note = request.data.get('note', '')
            appointment.status = 'CANCELLED'
            appointment.notes = f"Rejected by doctor: {note}"
            appointment.save()
            
            # Send notification to patient
            send_appointment_status_update.delay(appointment.id, "rejected", note)
            
            return Response({"status": "Appointment rejected"})
            
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        profile, created = Profile.objects.get_or_create(user=user)
        
        # Check if patient or doctor exists
        is_patient = hasattr(user, 'patient')
        is_doctor = hasattr(user, 'doctor')
        
        # Get patient/doctor data if exists
        patient_data = {}
        doctor_data = {}
        
        if is_patient:
            patient = user.patient
            patient_data = {
                'date_of_birth': patient.date_of_birth,
                'gender': patient.gender,
                'blood_type': patient.blood_type
            }
        
        if is_doctor:
            doctor = user.doctor
            doctor_data = {
                'specialty': doctor.specialty.id if doctor.specialty else None,
                'experience_years': doctor.experience_years,
                'consultation_fee': doctor.consultation_fee
            }
        
        serializer = ProfileSerializer(profile)
        response_data = serializer.data
        response_data.update({
            'is_patient': is_patient,
            'is_doctor': is_doctor,
            'profile_complete': user.profile_complete,
            'patient': patient_data,
            'doctor': doctor_data
        })
        
        return Response(response_data)
    
    def put(self, request):
        user = request.user
        profile = user.profile
        
        # Update patient data if exists
        patient_data = request.data.get('patient', {})
        if hasattr(user, 'patient'):
            patient = user.patient
            for field in ['date_of_birth', 'gender', 'blood_type']:
                if field in patient_data:
                    setattr(patient, field, patient_data[field])
            patient.save()
        
        # Update doctor data if exists
        doctor_data = request.data.get('doctor', {})
        if hasattr(user, 'doctor'):
            doctor = user.doctor
            for field in ['specialty', 'experience_years', 'consultation_fee']:
                if field in doctor_data:
                    setattr(doctor, field, doctor_data[field])
            doctor.save()
        
        # Update profile
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Return updated data with completion status
            response_data = serializer.data
            response_data.update({
                'is_patient': hasattr(user, 'patient'),
                'is_doctor': hasattr(user, 'doctor'),
                'profile_complete': user.profile_complete
            })
            return Response(response_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAuthenticated]
    
class VitalSignsViewSet(viewsets.ModelViewSet):
    queryset = VitalSigns.objects.all()
    serializer_class = VitalSignsSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('patient', 'recorded_at')

class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('patient', 'icd_code', 'status')

class MedicationViewSet(viewsets.ModelViewSet):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('patient', 'active')

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
