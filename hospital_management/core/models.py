from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

class User(AbstractUser):
    ROLE_CHOICES = [
        ('PATIENT', 'Patient'),
        ('DOCTOR', 'Doctor'),
        ('ADMIN', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='PATIENT')
    email_verified = models.BooleanField(default=False)
    
    # Resolve conflicts by adding custom related_names
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='custom_user_set',
        related_query_name='custom_user'
    )

    token_relationships = models.ManyToManyField(
        'token_blacklist.OutstandingToken',
        related_name='user_tokens',
        blank=True
    )

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ]
    
    BLOOD_TYPES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-')
    ]

    mrn = models.CharField(max_length=10, unique=True, null=True)  # Medical Record Number
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField(default=timezone.now)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="O")
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, default='0+')
    address = models.TextField()
    phone = models.CharField(max_length=15)
    emergency_contact = models.CharField(max_length=100, default="None")
    emergency_phone = models.CharField(max_length=15, default="None")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

class VitalSigns(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    temperature = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        validators=[MinValueValidator(35.0), MaxValueValidator(42.0)]
    )
    blood_pressure_systolic = models.IntegerField()
    blood_pressure_diastolic = models.IntegerField()
    heart_rate = models.IntegerField()
    respiratory_rate = models.IntegerField()
    oxygen_saturation = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

class Diagnosis(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    icd_code = models.CharField(max_length=10)
    description = models.TextField()
    diagnosed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    diagnosed_date = models.DateField()
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)

class Medication(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    prescribed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    active = models.BooleanField(default=True)


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=255)  # The affected resource/endpoint
    details = models.TextField(null=True, blank=True)  # Additional details about the action
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

class PatientHistory(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    change_date = models.DateTimeField(auto_now_add=True)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True)
    new_value = models.TextField(null=True)
    
    class Meta:
        ordering = ['-change_date']

class Specialty(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor')
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True)
    license_number = models.CharField(max_length=50, unique=True, default="Private")
    qualification = models.CharField(max_length=200, default="Private")
    experience_years = models.IntegerField(default=0)
    bio = models.TextField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    available_for_appointments = models.BooleanField(default=True)
    max_patients_per_day = models.IntegerField(default=20)
    
    def is_available(self, date, time):
        # Check if doctor is on leave
        leave_exists = DoctorLeave.objects.filter(
            doctor=self,
            start_date__lte=date,
            end_date__gte=date,
            status='APPROVED'
        ).exists()
        
        if leave_exists:
            return False
            
        # Check schedule
        day_of_week = date.weekday()
        schedule = DoctorSchedule.objects.filter(
            doctor=self,
            day_of_week=day_of_week,
            start_time__lte=time,
            end_time__gte=time,
            is_available=True
        ).exists()
        
        if not schedule:
            return False
            
        # Check number of appointments for that day
        appointments_count = Appointment.objects.filter(
            doctor=self,
            date=date,
            status='PENDING'
        ).count()
        
        return appointments_count < self.max_patients_per_day

class DoctorSchedule(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    day_of_week = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

class DoctorLeave(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(default="Emergency")
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('NO_SHOW', 'No Show')
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField(default="General Checkup")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        
    def save(self, *args, **kwargs):
        if not self.pk:  # New appointment
            if not self.doctor.is_available(self.appointment_date, self.appointment_time):
                raise ValueError("Doctor is not available at this time")
        super().save(*args, **kwargs)

class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='medical_records')
    diagnosis = models.TextField()
    prescription = models.TextField()
    notes = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)