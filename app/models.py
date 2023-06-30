from django.db import models
import random
from barcode import Code128
from barcode.writer import ImageWriter
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone
from django.core.validators import MinValueValidator


current_month = timezone.now().month
current_year = timezone.now().year

def generate_unique_id():
    # Generate a random 10 digit ID
    return str(random.randint(1000000000, 9999999999))

class Company(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    owner = models.CharField(max_length=255, null=True, blank=True)
    cost = models.CharField(max_length=255, default=0)


class CompanySubscription(models.Model):
    cost = models.CharField(max_length=255, default=0)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.company.name

class Profile(models.Model):
    LEVELS = (
        ('admin', "Administrator"),
        ('casher', "Kassir"),
        ('teacher', "O'qituvchi"),
        ('null', "Lavozim mavjud emas")
    )


    name = models.CharField(max_length=255, null=True, blank=True, default="F.I.Sh.")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255)
    level = models.CharField(choices=LEVELS, max_length=10, default='null')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_manager = models.BooleanField(default=False)
    
    barcode = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name
    
    def bonus_amount(self, month):
        balance = TeacherBonus.objects.filter(
            teacher=self, date__month=month, date__year=current_year).aggregate(Sum('amount'))
        return balance['amount__sum'] or 0
    
    def fine_amount(self, month):
        balance = TeacherFine.objects.filter(
            teacher=self, date__month=month, date__year=current_year).aggregate(Sum('amount'))
        return balance['amount__sum'] or 0
    
    def debt_amount(self, month):
        balance = TeacherDebt.objects.filter(
            teacher=self, date__month=month, date__year=current_year).aggregate(Sum('amount'))
        return balance['amount__sum'] or 0
    
    def attendace_amount(self, month):
        balance = TeacherAttendace.objects.filter(
            teacher=self, date__month=month, date__year=current_year).aggregate(Sum('amount'))
        return balance['amount__sum'] or 0
    

    def save(self, *args, **kwargs):
        if not self.barcode:
            # Generate a unique ID for the barcode
            barcode_id = self.phone

            # Generate the barcode as a Code128 code
            code = Code128(barcode_id, writer=ImageWriter())

            # Save the barcode as a PNG image
            filename = f"media/barcodes/{barcode_id}.png"
            code.save(filename)

            # Save the barcode filename to the database
            self.barcode = filename

        super(Profile, self).save(*args, **kwargs)


class Subject(models.Model):
    STATUS_TYPES = (
        ('0', "O'chirilgan"),
        ('1', "Aktiv")
    )
    name = models.CharField(max_length=255)
    status = models.CharField(choices=STATUS_TYPES, max_length=15)

    def __str__(self):
        return self.name


class Student(models.Model):
    student_id = models.CharField(max_length=10, default=generate_unique_id, unique=True)
    STATUS_TYPES = (
        ('0', "O'chirilgan"),
        ('1', "Aktiv")
    )

    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255)
    status = models.CharField(choices=STATUS_TYPES, max_length=15, default='1')
    sms_service = models.BooleanField(default=False)

    barcode = models.CharField(max_length=255, blank=True)

    def save(self, *args, **kwargs):
        if not self.barcode:
            # Generate a unique ID for the barcode
            barcode_id = self.student_id

            # Generate the barcode as a Code128 code
            code = Code128(barcode_id, writer=ImageWriter())

            # Save the barcode as a PNG image
            filename = f"media/barcodes/{barcode_id}.png"
            code.save(filename)

            # Save the barcode filename to the database
            self.barcode = filename
        
        super(Student, self).save(*args, **kwargs)


    def __str__(self):
        return f"{self.name} - {self.phone}"


class Group(models.Model):
    STATUS_TYPES = (
        ('0', "O'chirilgan"),
        ('1', "Aktiv")
    )

    name = models.CharField(max_length=255)
    cost = models.CharField(max_length=255, null=True, blank=True, default=0)
    students = models.ManyToManyField(Student, default='Talaba kiritilmagan', null=True, blank=True)
    teacher = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, null=True, blank=True)
    status = models.CharField(choices=STATUS_TYPES, max_length=15)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    STATUS_TYPES = (
        ('0', "O'chirilgan"),
        ('1', "Aktiv")
    )
    cost = models.CharField(max_length=255)
    month = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group, on_delete=models.PROTECT)
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_TYPES, max_length=15)
    
    def __str__(self):
        return self.student.name


class CompanySettings(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    attendace = models.BooleanField(default=False)
    payment = models.BooleanField(default=False)
    mark = models.BooleanField(default=False)

    api_link = models.CharField(max_length=280, null=True, blank=True)
    originator = models.CharField(max_length=255, null=True, blank=True)
    key = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.company.name



class TeacherBonus(models.Model):
    teacher = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.CharField(max_length=255)
    amount = models.CharField(max_length=255, default=0)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.teacher.name
    

class TeacherFine(models.Model):
    teacher = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.CharField(max_length=255)
    amount = models.CharField(max_length=255, default=0)
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.teacher.name
    

class TeacherDebt(models.Model):
    teacher = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.CharField(max_length=255)
    amount = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.teacher.name
    

class TeacherAttendace(models.Model):
    teacher = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.teacher.name


class Expense(models.Model):
    amount = models.IntegerField()
    comment = models.CharField(max_length=255)

    company = models.ForeignKey(Company, on_delete=models.CASCADE)


    date = models.DateTimeField(auto_now=True)
