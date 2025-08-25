from rest_framework import serializers
from .models import User, Patient, Doctor, Appointment, MedicalRecord, VitalSigns, Diagnosis, Medication, DoctorSchedule, DoctorLeave, Specialty, Profile
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate
from django.apps import apps
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
class UserSerializer(serializers.ModelSerializer):
    profile_complete = serializers.BooleanField(read_only=True)  # Add this field
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'profile_complete']  # Add profile_complete
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        try:
            # Try to fetch user by username
            self.user = User.objects.get(username=attrs.get(self.username_field))
            
            # Check password
            if not self.user.check_password(attrs.get('password', '')):
                raise AuthenticationFailed('Invalid username or password')
                
            # Check activation status
            if not self.user.is_active:
                raise AuthenticationFailed("Account not activated. Please check your email.")
                
        except User.DoesNotExist:
            # Also check by email if username not found
            try:
                self.user = User.objects.get(email=attrs.get(self.username_field))
                if not self.user.check_password(attrs.get('password', '')):
                    raise AuthenticationFailed('Invalid email or password')
            except User.DoesNotExist:
                raise AuthenticationFailed("Invalid credentials")
        
        # Continue with standard validation
        data = super().validate(attrs)
        
        # Get profile completion status safely
        profile_complete = False
        try:
            profile_complete = self.user.profile_complete
        except AttributeError:
            # Handle case where profile_complete doesn't exist
            pass
        
        # Add additional claims
        data.update({
            'role': self.user.role,
            'user_id': self.user.id,
            'profile_complete': profile_complete,
            'username': self.user.username,
            'email': self.user.email,
        })
        
        # Add profile IDs safely
        try:
            if self.user.role == 'PATIENT':
                data['patient_id'] = self.user.patient.id
            elif self.user.role == 'DOCTOR':
                data['doctor_id'] = self.user.doctor.id
        except ObjectDoesNotExist:
            # Profiles might not exist yet
            pass

        return data

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ['id', 'patient', 'doctor', 'diagnosis', 'prescription', 'notes', 'date']

class VitalSignsSerializer(serializers.ModelSerializer):
    class Meta:
        model = VitalSigns
        fields = '__all__'

class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = '__all__'

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = '__all__'

class DoctorScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSchedule
        fields = '__all__'

class DoctorLeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorLeave
        fields = '__all__'

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    schedule = DoctorScheduleSerializer(many=True, read_only=True)
    specialty = SpecialtySerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = '__all__'
        read_only_fields = ('user',)

class AppointmentSerializer(serializers.ModelSerializer):
    
    doctor = DoctorSerializer(read_only=True)
    patient = PatientSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('patient', 'status', 'created_at', 'updated_at')

    def validate(self, data):
        # Only validate appointment_date if it's being updated
        appointment_date = data.get('appointment_date')
        
        # If this is a partial update and appointment_date is not provided, skip date validation
        if self.partial and appointment_date is None:
            return data
            
        # If appointment_date is provided, validate it
        if appointment_date is not None and appointment_date < timezone.now().date():
            raise serializers.ValidationError("Appointment date cannot be in the past")
        
        return data

    def create(self, validated_data):
        request = self.context.get('request')
        
        # Check if user is authenticated
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("User must be authenticated to book an appointment")
        
        # Get the patient associated with the user
        try:
            patient = Patient.objects.get(user=request.user)
        except Patient.DoesNotExist:
            raise serializers.ValidationError("Patient profile not found. Please complete your profile first.")
        
        # Set the patient for the appointment
        validated_data['patient'] = patient
        
        # Create and return the appointment
        return super().create(validated_data)
        

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'phone_number', 'address', 'city', 'country', 
            'profile_picture', 'bio', 'emergency_contact', 
            'emergency_phone', 'license_number', 'qualifications'
        ]
        extra_kwargs = {
            'profile_picture': {'required': False}
        }