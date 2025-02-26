from rest_framework import viewsets, status
from .models import Patient, Doctor, Appointment, MedicalRecord, User, Diagnosis, VitalSigns, Medication, Specialty
from .serializers import PatientSerializer, DoctorSerializer, SpecialtySerializer, AppointmentSerializer, MedicalRecordSerializer, UserSerializer, CustomTokenObtainPairSerializer, MedicationSerializer, DiagnosisSerializer, VitalSignsSerializer
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.mail import send_mail
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
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

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                response_data = serializer.validated_data
                return Response(response_data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        except AuthenticationFailed as e:
            return Response(
                {"detail": str(e)}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"detail": "An error occurred during login"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"message": "Refresh token is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"message": "Successfully logged out."}, 
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
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
            
            subject = 'Verify Your Email'
            message = render_to_string('verify_email.html', {
                'user': user,
                'verification_link': verification_link,
            })
            send_mail(subject, message, 'noreply@hospital.com', [user.email])
            
            return Response({
                'message': 'Registration successful. Please verify your email.',
                'user_id': user.id,
                'role': user.role
            }, status=status.HTTP_201_CREATED)
            
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView1(APIView):
    def post(self, request, uidb64, token):
        try:
            # Decode uid
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            # Validate token
            if default_token_generator.check_token(user, token):
                user.email_verified = True
                user.is_active = True
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)
            else:
                return Response({'message': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'message': 'Invalid user.'}, status=status.HTTP_400_BAD_REQUEST)

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
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        doctor = self.get_object()
        date = request.query_params.get('date')
        
        try:
            date = datetime.strptime(date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        schedule = doctor.doctorschedule_set.filter(
            day_of_week=date.weekday(),
            is_available=True
        )
        
        available_slots = []
        for slot in schedule:
            current_time = slot.start_time
            while current_time < slot.end_time:
                if doctor.is_available(date, current_time):
                    available_slots.append(current_time.strftime('%H:%M'))
                current_time = (
                    datetime.combine(date, current_time) + 
                    timedelta(minutes=30)
                ).time()
        
        return Response({"available_slots": available_slots})

class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'DOCTOR':
            return Appointment.objects.filter(doctor__user=user)
        elif user.role == 'PATIENT':
            return Appointment.objects.filter(patient__user=user)
        return Appointment.objects.all()
    
    def perform_create(self, serializer):
        appointment = serializer.save()
        send_appointment_confirmation.delay(appointment.id)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'CANCELLED'
        appointment.save()
        return Response({"status": "Appointment cancelled"})

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
