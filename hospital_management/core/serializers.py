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
    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ('status', 'created_at', 'updated_at')

    def validate(self, data):
        doctor = data['doctor']
        appointment_date = data['appointment_date']
        appointment_time = data['appointment_time']
        
        if not doctor.is_available(appointment_date, appointment_time):
            raise serializers.ValidationError("Doctor is not available at this time")
        
        return 
        
class ProfileSerializerz(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    role = serializers.CharField(source='user.role')
    
    # Patient-specific fields (accessed through user)
    mrn = serializers.CharField(source='user.patient.mrn', read_only=True, allow_null=True)
    date_of_birth = serializers.DateField(source='user.patient.date_of_birth', allow_null=True)
    gender = serializers.CharField(source='user.patient.gender', allow_null=True)
    blood_type = serializers.CharField(source='user.patient.blood_type', allow_null=True)
    
    # Doctor-specific fields (accessed through user)
    specialty = serializers.PrimaryKeyRelatedField(
        source='user.doctor.specialty', 
        queryset=Specialty.objects.all(),
        allow_null=True
    )
    experience_years = serializers.IntegerField(
        source='user.doctor.experience_years',
        allow_null=True
    )
    consultation_fee = serializers.DecimalField(
        source='user.doctor.consultation_fee',
        max_digits=10,
        decimal_places=2,
        allow_null=True
    )

    class Meta:
        model = Profile
        fields = [
            'username', 'email', 'role', 'phone_number', 'address', 'city',
            'country', 'profile_picture', 'bio', 'emergency_contact',
            'emergency_phone', 'license_number', 'qualifications',
            'mrn', 'date_of_birth', 'gender', 'blood_type',
            'specialty', 'experience_years', 'consultation_fee'
        ]
        extra_kwargs = {
            'mrn': {'required': False},
            'date_of_birth': {'required': False},
            'gender': {'required': False},
            'blood_type': {'required': False},
            'specialty': {'required': False},
            'experience_years': {'required': False},
            'consultation_fee': {'required': False}
        }

    def update(self, instance, validated_data):
        # Extract nested data
        user_data = validated_data.pop('user', {})
        patient_data = user_data.pop('patient', {}) if 'user' in validated_data else {}
        doctor_data = user_data.pop('doctor', {}) if 'user' in validated_data else {}

        # Update User
        user = instance.user
        user.username = user_data.get('username', user.username)
        user.email = user_data.get('email', user.email)
        user.save()

        # Update Patient if exists
        if hasattr(user, 'patient'):
            patient = user.patient
            for attr, value in patient_data.items():
                setattr(patient, attr, value)
            patient.save()

        # Update Doctor if exists
        if hasattr(user, 'doctor'):
            doctor = user.doctor
            for attr, value in doctor_data.items():
                setattr(doctor, attr, value)
            doctor.save()

        # Update Profile
        return super().update(instance, validated_data)

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