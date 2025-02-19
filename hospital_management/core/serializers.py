from rest_framework import serializers
from .models import User, Patient, Doctor, Appointment, MedicalRecord, VitalSigns, Diagnosis, Medication, DoctorSchedule, DoctorLeave, Specialty
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import AuthenticationFailed
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate
from django.apps import apps

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        try:
            self.user = User.objects.get(username=attrs[self.username_field])
            
            if not self.user.check_password(attrs['password']):
                raise AuthenticationFailed('Invalid credentials')
                
            if not self.user.is_active:
                raise AuthenticationFailed("Account not activated")
                
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid credentials")
        
        data = super().validate(attrs)
        data.update({
            'role': self.user.role,
            'user_id': self.user.id,
        })
        
        try:
            if self.user.role == 'PATIENT':
                data['patient_id'] = self.user.patient.id
            elif self.user.role == 'DOCTOR':
                data['doctor_id'] = self.user.doctor.id
        except ObjectDoesNotExist:
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
        
        return data
