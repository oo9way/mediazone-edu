from django.contrib import admin
from .models import Student, Group, Subject, Subscription, Profile, Company, CompanySubscription, CompanySettings, TeacherFine, TeacherBonus, TeacherDebt, TeacherAttendace

admin.site.register(Student)
admin.site.register(Group)
admin.site.register(Subject)
admin.site.register(Subscription)
admin.site.register(Profile)
admin.site.register(Company)
admin.site.register(CompanySubscription)
admin.site.register(CompanySettings)
admin.site.register(TeacherFine)
admin.site.register(TeacherDebt)
admin.site.register(TeacherBonus)
admin.site.register(TeacherAttendace)