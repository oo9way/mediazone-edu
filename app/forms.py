from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordChangeForm
from django.forms import models
from .models import Group, Student, Profile, CompanySettings
from django import forms
from django.utils.translation import gettext, gettext_lazy as _


class GroupCreationForm(models.ModelForm):
    class Meta:
        model = Group
        exclude = ['status', 'students', 'company', 'teacher']
        labels = {
            'name':'Guruh nomi',
            'teacher': "O'qituvchi",
            'subject':"Fan",
            'cost':"Kurs narxi"
        }

        widgets = {
            'students': forms.SelectMultiple(attrs={'class': 'js-example-basic-multiple'}),
        }


class GroupEditionForm(models.ModelForm):

    def __init__(self, profile=None, **kwargs):
        super(GroupEditionForm, self).__init__(**kwargs)
        if profile:
            self.fields['students'].queryset = Student.objects.filter(
                company=profile.company, status='1')

    class Meta:
        model = Group
        fields = ['name', 'students', 'subject', 'cost']
        labels = {
            'name': 'Guruh nomi',
            'students': "Talabalar",
            'teacher': "O'qituvchi",
            'subject': "Fan",
            'cost': "Narx"
        }

        widgets = {
            'students': forms.SelectMultiple(attrs={'class': 'js-example-basic-multiple'}),
        }



class TeacherCreationForm(models.ModelForm):
    class Meta:
        model = Profile
        exclude = ['is_active', 'company', 'is_manager', 'level', 'user']
        labels = {
            'name': "F.I.Sh.",
            "subject": "Fan",
            'phone': "Telefon raqam, 978885522 formatida"
        }

class StudentCreationForm(models.ModelForm):
    class Meta:
        model = Student
        exclude = ['status', 'barcode', 'student_id', 'company']
        labels = {
            "name": "F.I.Sh.",
            'phone': "Telefon raqam, 901234455 formatida",
            'sms_service':"SMS xizmati"
        }
        
        widgets = {
            'name': forms.TextInput(attrs={'autofocus': 'autofocus'}),
        }

class CompanySettingsForm(models.ModelForm):
    class Meta:
        model = CompanySettings
        exclude = ['company']



class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Hozirgi parol",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(
        label=_("Yangi parol"),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("Yangi parolni tasdiqlang"),
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].help_text = gettext(
            password_validation.password_validators_help_text_html())

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                gettext('Hozirgi parol xato kiritildi.'))
        return old_password

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError(
                gettext('Yangi parollar bir xil emas.'))
        password_validation.validate_password(new_password2, self.user)
        return new_password2
