from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
import random

from hospital.constants import PaymentStatus

departments = [
    ('Cardiologist', 'Cardiologist'),
    ('Dermatologists', 'Dermatologists'),
    ('Emergency Medicine Specialists', 'Emergency Medicine Specialists'),
    ('Allergists/Immunologists', 'Allergists/Immunologists'),
    ('Anesthesiologists', 'Anesthesiologists'),
    ('Colon and Rectal Surgeons', 'Colon and Rectal Surgeons')
]

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    profile_pic = models.ImageField(upload_to='profile_pic/DoctorProfilePic/', null=True, blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=True)
    department = models.CharField(max_length=50, choices=departments, default='Cardiologist')
    status = models.BooleanField(default=False)

    @property
    def get_name(self):
        return self.user.get_full_name()

    @property
    def get_id(self):
        return self.user.id

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.department})"


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    profile_pic = models.ImageField(upload_to='profile_pic/PatientProfilePic/', null=True, blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=False)
    symptoms = models.CharField(max_length=100, null=False)
    assignedDoctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='patients')
    admitDate= models.DateField(auto_now=True)
    status = models.BooleanField(default=False)

    @property
    def get_name(self):
        return self.user.get_full_name()

    @property
    def get_id(self):
        return self.user.id

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.symptoms})"


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField(auto_now=True)
    description = models.TextField(max_length=500)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"Appointment for {self.patient.get_name()} with {self.doctor.get_name()} on {self.appointment_date}"


# class PatientDischargeDetails(models.Model):
#     patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name='discharge_details')
#     address = models.CharField(max_length=40)
#     mobile = models.CharField(max_length=20, null=True)
#     symptoms = models.CharField(max_length=100, null=True)
#     releaseDate = models.DateField(null=False)
#     daySpent = models.PositiveIntegerField(null=False)
#     roomCharge = models.PositiveIntegerField(null=False)
#     medicineCost = models.PositiveIntegerField(null=False)
#     doctorFee = models.PositiveIntegerField(null=False)
#     otherCharge = models.PositiveIntegerField(null=False)
#     total = models.PositiveIntegerField(null=False)
#     paid = models.BooleanField(default=False)
#     status = models.CharField(
#         _("Payment Status"),
#         default=PaymentStatus.PENDING,
#         max_length=254,
#         blank=False,
#         null=False,
#     )
#     provider_order_id = models.CharField(
#         _("Order ID"), max_length=40, null=False, blank=False
#     )
#     payment_id = models.CharField(
#         _("Payment ID"), max_length=36, null=False, blank=False
#     )
#     signature_id = models.CharField(
#         _("Signature ID"), max_length=128, null=False, blank=False
#     )
#
#     def __str__(self):
#         return f"Patient:} - Discharge Date: {self.release_date}"

class PatientDischargeDetails(models.Model):
    patient = models.OneToOneField('Patient', on_delete=models.CASCADE, related_name='discharge_details')
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20, null=True)
    symptoms = models.CharField(max_length=100, null=True)
    release_date = models.DateField()
    day_spent = models.PositiveIntegerField()
    room_charge = models.PositiveIntegerField()
    medicine_cost = models.PositiveIntegerField()
    doctor_fee = models.PositiveIntegerField()
    other_charge = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    paid = models.BooleanField(default=False)
    status = models.CharField(
        "Payment Status",
        default='Pending',
        max_length=254
    )
    provider_order_id = models.CharField(
        "Order ID", max_length=40
    )
    payment_id = models.CharField(
        "Payment ID", max_length=36
    )
    signature_id = models.CharField(
        "Signature ID", max_length=128
    )

    def __str__(self):
        # return f"Patient: {self.patient.get_name()} - Discharge Date: {self.release_date}"
        return f"Patient: - Discharge Date: {self.release_date}"


class Account(models.Model):
    holder = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    account_number = models.CharField(max_length=20, unique=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=10000.00)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('Active', 'Active'), ('Inactive', 'Inactive')])

    def __str__(self):
        return f"{self.holder.get_full_name()} - {self.account_number} - {self.balance}"

    class Meta:
        ordering = ['-date']


class Payment(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='payments')
    bill = models.OneToOneField(PatientDischargeDetails, on_delete=models.CASCADE, related_name='payment')
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')])
    transaction_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        super().save(*args, **kwargs)

    def generate_transaction_id(self):
        random_number = random.randint(10000000, 99999999)
        return random_number

    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.amount} - {self.status} - {self.transaction_id}"

    class Meta:
        ordering = ['-date']
