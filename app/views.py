from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from .models import Group, Student, Subscription, Profile, Subject, CompanySettings, CompanySubscription, TeacherBonus, TeacherDebt, TeacherFine, Expense, TeacherAttendace
from .forms import GroupCreationForm, GroupEditionForm, TeacherCreationForm, StudentCreationForm, CompanySettingsForm, CustomPasswordChangeForm
from django.contrib import  messages
from django.contrib.auth import login, logout, authenticate
from django.urls import reverse
from pytz import UTC


from django.db.models import Count, Q, Sum
from django.contrib.auth.forms import PasswordChangeForm
from datetime import date, datetime, timedelta
from utils import send_msg
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.transaction import atomic


def is_valid_date(date_string, date_format):
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False



def check_sub(profile):
    today = datetime.today()
    first_day_of_month = datetime(today.year, today.month, 1)
    days_since_first_day = (today - first_day_of_month).days
    current_month = datetime.now().month
    current_year = datetime.now().year
    subsciption = CompanySubscription.objects.filter(company=profile.company).filter(date__month=current_month, date__year=current_year)
    
    if len(subsciption) == 1:
        return True
    else:
        return days_since_first_day

def login_page(request):
    if request.user.is_authenticated:
        error_message = ''
        user = request.user
        profile = Profile.objects.get(user=user)

        if profile.is_manager:
                return redirect('manager:companies')
        else:
            if profile.level == 'admin':
                return redirect('app:admin-home')
            elif profile.level == 'casher':
                return redirect('app:home')
            
            elif profile.level == 'teacher':
                return redirect('app:teacher-home')

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            user = User.objects.get(username=username)
            try:
                profile = Profile.objects.get(user=user)
            except:
                profile = Profile.objects.create(
                    name=username,
                    phone='null',
                    user=user,
                    level='null',
                    is_active=True,
                    is_manager=True
                )
            
            if profile.is_active:
                login(request, user)
                
                messages.success(request, "Kabinetga xush kelibsiz")
                if profile.is_manager:
                    return redirect('manager:companies')
                else:
                    if profile.level == 'admin' and not profile.is_manager:
                        return redirect('app:admin-home')
                    elif profile.level == 'casher' and not profile.is_manager:
                        return redirect('app:home')
                    elif profile.level == 'teacher' and not profile.is_manager:
                        return redirect('app:teacher-home')
                    
            else:
                messages.error(request, "Profil aktiv emas", extra_tags='danger')
                return redirect('app:login')
        else:
            error_message = 'Login yoki parol xato'
    else:
        error_message = ''
    return render(request, 'login.html', {'error_message': error_message})

def logout_page(request):
    logout(request)
    return redirect('app:login')


@login_required(login_url='app:login', redirect_field_name='home')
def subscibe_page(request):
    if request.user.is_authenticated:
        user = request.user
        profile = Profile.objects.get(user=user)

        if profile.is_manager or request.user.is_staff:
            return redirect('manager:companies')
        else:
            if profile.level == 'admin' and (check_sub(profile) == True or check_sub(profile) <= 5):
                return redirect('app:admin-home')
            elif profile.level == 'casher' and (check_sub(profile) == True or check_sub(profile) <= 5):
                return redirect('app:home')

            elif profile.level == 'teacher' and (check_sub(profile) == True or check_sub(profile) <= 5) :
                return redirect('app:teacher-home')
    manager = Profile.objects.get(is_manager=True)
    return render(request, 'subscribe.html', {'manager':manager})

@login_required(login_url='app:login', redirect_field_name='home')
def home(request):
    profile = Profile.objects.get(user=request.user)
    if profile.level == 'casher':
        if check_sub(profile) == True or check_sub(profile) <=5:
            current_day = f"{datetime.now().hour}:{datetime.now().minute}"
            current_month = date.today().month
            current_year = date.today().year

            student = False
            success = None
            teacher = False
            sub_year = None
            unpayed = None
            if 'id' in request.GET:
                try:
                    student = Student.objects.get(
                        student_id=request.GET['id'], company=profile.company)
                except:
                    student = None

                if student == None:
                    try:
                        teacher = Profile.objects.get(company=profile.company, phone=request.GET['id'])
                        teacher_attendace = TeacherAttendace.objects.filter(teacher=teacher, date__day=date.today().day, date__month=date.today().month, date__year=date.today().year)
                        if len(teacher_attendace) == 0:
                            TeacherAttendace.objects.create(teacher=teacher, amount=1)

                    except:
                        teacher = None

                if student:
                    if profile.company.companysettings_set.first() != None and profile.company.companysettings_set.first().attendace and student.sms_service:
                        attendace_message = f"{student.name} {current_day} da o'quv markaziga keldi.\nSana: {datetime.now().day}-{datetime.now().strftime('%B')}"
                        send_msg(profile, f"998{student.phone}",
                                attendace_message, 'attendace')
                    sub = Subscription.objects.filter(company=profile.company).filter(month__month=current_month).filter(
                        student=student).filter(status='1').filter(month__year=current_year)

                    groups = Group.objects.filter(
                        company=profile.company).filter(students=student)
                    sub_year = Subscription.objects.filter(company=profile.company).filter(
                        month__year=current_year).filter(student=student).filter(status='1')
                    unpayed = []
                    unpayed_groups = []
                    for p in sub:
                        unpayed_groups.append(p.group)

                    for gr in student.group_set.all():
                        if gr not in unpayed_groups:
                            unpayed.append(gr)

                    if len(sub) >= len(groups):
                        success = True
                    else:
                        success = False


            if request.method == "POST":
                text_messages = "To'lov qabul qilindi."
                # try:
                amount = int(request.POST['amount'])
                for i in range(1, amount+1):
                    u_group = Group.objects.get(
                        id=request.POST[f'group{i}'], company=profile.company)

                    if len(request.POST[f"sum{i}"]) > 0:
                        u_sum = int(request.POST[f'sum{i}'])
                    else:
                        u_sum = 0

                    if u_sum > 0:
                        Subscription.objects.create(
                            cost=u_sum,
                            group=u_group,
                            student=student,
                            company=profile.company,
                            status='1'
                        )
                        text_messages += f"\nKurs nomi - {u_group.name}.\nTo'lov miqdori - {u_sum} so'm.\n"

                    if profile.company.companysettings_set.first() and profile.company.companysettings_set.first().payment and student.sms_service:
                        send_msg(profile, f'998{student.phone}',
                                text_messages, 'payment')
                    messages.success(request, "To'lov ro'yxatga olindi")
                # except:
                #     messages.error(request, "Xatolik ketdi, qaytadan urining", extra_tags='danger')

                return redirect(f'/?id={student.student_id}')

            context = {
                'student': student,
                'teacher':teacher,
                'success': success,
                'sub_year': sub_year,
                'unpayed': unpayed
            }

            return render(request, 'home/index.html', context)
        else:
            return redirect("app:subscribe")

    else:
        return redirect("app:login")


@login_required(login_url='app:login', redirect_field_name='datas')
def datas(request):
    profile = Profile.objects.get(user=request.user)
    if profile.level == 'casher':
        if check_sub(profile) == True or check_sub(profile) <= 5:
            current_month = datetime.now().month
            current_year = datetime.now().year

            groups = Group.objects.annotate(
                subscription_count=Count(
                    'subscription',
                    filter=Q(subscription__month__month=current_month) &
                    Q(subscription__month__year=current_year) &
                    Q(subscription__status='1')
                )
            ).filter(status='1').filter(company=profile.company)
            all_students = 0
            payed_students = 0
            for g in groups:
                all_students += g.students.count()
                payed_students += g.subscription_count

            subs = Subscription.objects.filter(company=profile.company).filter(Q(month__month=current_month) & Q(month__year=current_year))
            
            context = {
                'groups': groups,
                'date':datetime.now(),
                'unpayed':all_students - payed_students
            }
            return render(request, 'data/index.html', context)
        else:
            return redirect("app:subscribe")
    else:
        return redirect('app:login')

@login_required(login_url='app:login', redirect_field_name='datas')
def group(request, pk):
    profile = Profile.objects.get(user=request.user)
    if profile.level == 'casher' or profile.level == 'admin':
        if check_sub(profile) == True or check_sub(profile) <= 5:
            current_month = datetime.now().month
            current_year = datetime.now().year
            try:
                group = Group.objects.get(id=pk, status='1', company=profile.company)
                check_status = group.students.filter(subscription__month__month=current_month, subscription__month__year=current_year).filter(subscription__group=group)
            except:
                messages.error(request, "Xatolik, guruh topilmadi", extra_tags='danger')
                return redirect('app:datas')
            context = {
                'group':group,
                'check_status':check_status
            }
            return render(request, 'data/group.html', context)
        else:
            return redirect('app:subscribe')
    else:
        return redirect('app:login')

@login_required(login_url='app:login', redirect_field_name='datas')
def print_group(request, pk):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        group = None
        if profile.level == 'casher':
            status = None
            try:
                if 'mode' in request.GET:
                    if request.GET['mode'] == 'teachers':
                        status = 'teacher'
                        group = Profile.objects.filter(level='teacher', company=profile.company)
                    else:
                        return redirect('app:datas')
                else:
                    status = 'student'
                    group = Group.objects.get(id=pk, company=profile.company)
            except:
                messages.error(request, "Xatolik, guruh topilmadi", extra_tags='danger')
                return redirect('app:datas')
        
        if profile.level == 'teacher':
            try:
                group = Group.objects.get(id=pk, company=profile.company, teacher=profile)
            except:
                messages.error(request, "Xatolik, guruh topilmadi", extra_tags='danger')
                return redirect('app:teacher-home')
        
        context = {
            'group': group,
            'status':status,
        }
        return render(request, 'data/print.html', context)
    else:
        return redirect('app:subscribe')


@login_required(login_url='app:login', redirect_field_name='data*/create-group')
def create_group(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        teachers = Profile.objects.filter(company=profile.company, level='teacher')
        if profile.level == 'casher':
            form = GroupCreationForm
            if request.method == "POST":
                
                form = GroupCreationForm(request.POST)
                if form.is_valid():
                    group = form.save(commit=False)
                    try:
                        teacher = Profile.objects.get(id=request.POST['teacher'])
                        group.teacher = teacher
                    except:
                        pass

                    group.status = '1'
                    group.company = profile.company
                    group.save()
                    messages.success(request, "Guruh ro'yxatga olindi")
                    return redirect('app:datas')

            context = {'form': form, 'page_name':"Guruhlar", 'teachers':teachers}
            return render(request, 'data/form.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='datas')
def edit_group(request, pk):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:

        if profile.level == 'casher':
            try:
                group = Group.objects.get(id=pk)
                teachers = Profile.objects.filter(company=profile.company, is_active=True, level='teacher')
                students = Student.objects.filter(company=profile.company, status='1')
                form = GroupEditionForm(instance=group, profile=profile)
            except:
                messages.error(request, "Xatolik, qaytadan urining", extra_tags='danger')
                return redirect('app:datas')
            if request.method == "POST":
                form = GroupEditionForm(data=request.POST, profile=profile, instance=group)
                if form.is_valid():
                    form.save()
                    try:
                        teacher = Profile.objects.get(is_active=True, level='teacher', company=profile.company, id=request.POST['teacher'])
                        group.teacher = teacher
                        group.save()
                    except:
                        pass
                    messages.success(request, "Guruhga o'zgartirish kiritildi")
                else:
                    messages.error(request, "Xatolik, formada xatolik bor", extra_tags='danger')

                return redirect('app:datas')
        
        
            context = {
                'form': form,
                'teachers': teachers,
                'page_name': "Guruhlar",
                'students': students
            }
            return render(request, 'data/form.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')
    

@login_required(login_url='app:login', redirect_field_name='datas')
def delete_group(request, pk):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:

        if profile.level == 'casher':

            try:
                group = Group.objects.get(id=pk, company=profile.company)
            except:
                messages.error(request, "Xatolik, qaytadan urining", extra_tags='danger')
                return redirect('app:datas')
            if request.method == "POST":
                group.status = 0
                group.students.set([])
                group.save()
                messages.success(request, "Guruh o'chirildi")
                return redirect('app:datas')
            context = {
                'group': group,
                'page_name': "Guruhlar"
            }
            return render(request, 'data/delete.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')


@login_required(login_url='app:login', redirect_field_name='home')
def teachers(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:

        if profile.level == 'casher' or profile.level == 'admin':

            teachers_all = Profile.objects.filter(is_active=True, level='teacher').filter(company=profile.company)
            context = {
                'teachers': teachers_all,
            }
            return render(request, 'data/teachers.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='home')
def create_teacher(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:

        if profile.level == 'casher':

            form = TeacherCreationForm
            if request.method == "POST":
                form = TeacherCreationForm(request.POST)
                if form.is_valid():
                    try:
                        teacher_user = User.objects.create_user(
                            username=request.POST['phone'], password=request.POST['password'])
                        teacher = form.save(commit=False)
                        teacher.user = teacher_user
                        teacher.level = 'teacher'
                        teacher.is_active = True
                        teacher.company = profile.company
                        teacher.save()
                        messages.success(request, "O'qituvchi ro'yxatga olindi")
                    except:
                        messages.error(request, "Xatolik, ushbu raqam boshqa foydalanuvchiga tegishli", extra_tags='danger')
                        return redirect('app:teachers')
                else:
                    messages.error(request, "Xatolik, formada xatolik bor", extra_tags='danger')
                return redirect('app:teachers')
            context = {
                'form': form,
                'page_name': "O'qituvchilar",
                'phone': True
            }
            return render(request, 'data/form.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='home')
def edit_teacher(request, pk,):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:

        if profile.level == 'casher' or profile.level == 'admin':

            try:
                teacher = Profile.objects.get(id=pk, company=profile.company, level='teacher')
                form = TeacherCreationForm(instance=teacher)
            except:
                messages.error(request, "Xatolik, qaytadan urining", extra_tags='danger')
                return redirect('app:teachers')
            if request.method == "POST":
                with atomic():
                    form = TeacherCreationForm(request.POST, instance=teacher)
                    if form.is_valid():
                        form.save()
                        messages.success(request, "O'zgartirish kiritildi")
                    else:
                        messages.error(
                            request, "Xatolik, formada xatolik bor", extra_tags='danger')

                    try:
                        teacher_user = User.objects.get(username=teacher.user.username)
                        teacher_user.username = request.POST['phone']
                        teacher_user.save()
                    except:
                        messages.error(
                            request, "Xatolik, ushbu raqamda foydalanuvchi mavjud", extra_tags='danger')

                    return redirect(f'app:teachers')

            context = {
                'form': form,
                'page_name': "O'qituvchilar"
            }
            return render(request, 'data/form.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe') 


@login_required(login_url='app:login', redirect_field_name='home')
def edit_student(request, pk,):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:

        if profile.level == 'casher' or profile.level == 'admin' or profile.level == 'teacher':
            try:
                student = Student.objects.get(id=pk, company=profile.company)
                form = StudentCreationForm(instance=student)
            except:
                messages.error(request, "Xatolik, talaba topilmadi", extra_tags='danger')
                return redirect('app:datas')
            if request.method == "POST":
                with atomic():
                    form = StudentCreationForm(data=request.POST, instance=student)
                    if form.is_valid():
                        form.save()
                        messages.success(request, "O'zgartirish saqlandi")
                    else:
                        messages.error(request, "Xatolik, formada xatolik bor", extra_tags="danger")
                    return redirect('app:datas')
            context = {
                'form':form,
                'page_name':student.name
            }
            return render(request, 'data/form.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='home')
def delete_teacher(request, pk):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:

        if profile.level == 'casher' or profile.level == 'admin':

            try:
                teacher = Profile.objects.get(id=pk, company=profile.company, level='teacher')
            except:
                messages.error(request, "Xatolik, qaytadan urining", extra_tags='danger')
                return redirect('app:teachers')
            if request.method == "POST":
                teacher_username = teacher.user.username
                teacher.delete()
                user = User.objects.get(username=teacher_username)
                user.delete()
                messages.success(request, "O'qituvchi o'chirildi")
                return redirect('app:teachers')
            context = {
                'group': teacher,
                'page_name': "Guruhlar"
            }
            return render(request, 'data/delete.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')
    

@login_required(login_url='app:login', redirect_field_name='home')
def create_student(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:

        if profile.level == 'casher':

            form = StudentCreationForm

            if request.method == "POST":
                form = StudentCreationForm(request.POST)
                if form.is_valid():
                    student = form.save(commit=False)
                    student.company = profile.company
                    student.save()
                    messages.success(request, "O'quvchi kiritildi")
                else:
                    messages.error(request, "Formada xatolik bor", extra_tags='danger')
                return redirect('app:create-student')
            context = {
                'form': form,
                'page_name': "O'quvchi kiritish"
            }
            return render(request, 'data/form.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')
    

@login_required(login_url='app:login', redirect_field_name='home')
def daily_history(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher' or profile.level == 'admin':
            current_day = datetime.today().day
            current_month = datetime.today().month
            current_year = datetime.today().year
            subs = Subscription.objects.filter(company=profile.company).filter(month__day=current_day, month__month=current_month, month__year=current_year).order_by('-month')
            total =  subs.aggregate(Sum('cost'))['cost__sum']
            if 'month' in request.GET and profile.level == 'admin':
                try:
                    current_month = int(request.GET['month'])
                except:
                    current_month = date.today().month
                
                subs = Subscription.objects.filter(company=profile.company).filter(month__month=current_month).order_by('-month')
                total =  subs.aggregate(Sum('cost'))['cost__sum']

            
            if 'date' in request.GET and profile.level == 'casher':
                if is_valid_date(request.GET['date'], '%Y-%m-%d'):
                    current_day = request.GET['date']
                    subs = Subscription.objects.filter(company=profile.company).filter(month__date=current_day).order_by('-month')
                    total =  subs.aggregate(Sum('cost'))['cost__sum']

                else:
                    current_day = datetime.today().day
            context = {
                'subs':subs,
                'total':total,
            }
            return render(request, 'data/history.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')


@login_required(login_url='app:login', redirect_field_name='home')
def groups_list(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher':

            groups = Group.objects.filter(status='1').filter(company=profile.company)
            context ={
                'groups':groups
            }
            return render(request, 'data/groups_list.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')


@login_required(login_url='app:login', redirect_field_name='home')
def send_message(request, pk):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher' or profile.level == 'teacher':
            if profile.level =='casher':
                try:
                    group = Group.objects.get(id=pk, status='1', company=profile.company)
                except:
                    messages.error(request, "Xatolik, guruh topilmadi", extra_tags='danger')
                    return redirect('app:message-groups')
            
            if profile.level == 'teacher':
                try:
                    group = Group.objects.get(id=pk, status='1', company=profile.company, teacher=profile)
                except:
                    messages.error(request, "Xatolik, guruh topilmadi", extra_tags='danger')
                    return redirect('app:teacher-home')

            
            if request.method == "POST":
                if profile.company.companysettings_set.first().mark:
                    counter = request.POST['counter']
                    for i in range(1, int(counter)+1):
                        student = Student.objects.get(id=request.POST[f'student{i}'])
                        numberid = 'tel'+str(i)
                        textid = 't'+str(i)
                        reciever = '998'+request.POST[numberid]
                        text = request.POST[textid]
                        if student.sms_service:
                            send_msg(profile, reciever, text, 'mark')
                    messages.success(request, "Xabarlar yuborildi")
                else:
                    messages.error(request, "Xabar yuborish o'chirilgan", extra_tags='danger')
                
                if profile.level == 'casher':
                    return redirect('app:message-groups')
                
                if profile.level =='teacher':
                    return redirect('app:teacher-home')
            
            context = {
                'group':group,
                'view':'1'
            }

            return render(request, 'data/send_message.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='home')
def user_settings(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher':
            form = CustomPasswordChangeForm(user=request.user)
            if request.method == "POST":
                if request.POST['action'] == 'info':
                    username = request.POST['username']
                    fullname = request.POST['fullname']

                    users = User.objects.filter(
                        username=username)
                    if request.user.username != username and len(users) > 0:
                        messages.error(
                            request, "Siz kiritgan login boshqa foydalanuvchiga tegishli", extra_tags='danger')
                    elif request.user.username != username:
                        user = User.objects.get(username=request.user.username)
                        user.username = username
                        user.save()
                        messages.success(
                            request, "Login muvaffaqiyatli o'zgartirildi")

                    profile = Profile.objects.get(user__username=username)
                    profile.name = fullname
                    profile.save()

                    return redirect('app:admin-profile')
                elif request.POST['action'] == 'password':
                    form = CustomPasswordChangeForm(
                        user=request.user, data=request.POST)
                    if form.is_valid():
                        user = form.save()
                        update_session_auth_hash(request, user)  # Important!
                        messages.success(
                            request, 'Parol muvaffaqiyatli o`zgartirildi!')
                        return redirect('app:admin-home')
                else:
                    form = CustomPasswordChangeForm(user=request.user)

            return render(request, 'settings/settings.html', {'form': form})
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='home')
def change_password(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        errors = ""
        if profile.level == 'casher' or profile.level == 'admin':

            if request.method == 'POST':
                form = PasswordChangeForm(user=request.user, data=request.POST)
                if form.is_valid():
                    form.save()
                    messages.success(request, 'Parol muvaffaqiyatli o`zgartirildi.')
                else:
                    errors = form.errors()

                    messages.error(request, f"Xatolik,", extra_tags='danger')
            if profile.level =='casher':
                return redirect('app:settings')
            if profile.level == 'admin':
                return redirect('app:admin-profile')
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='home')
def get_cheque(request, pk):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher':

            s = Subscription.objects.get(id=pk, company=profile.company)
            context = {'s':s}
            return render(request, 'data/cheque.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')
    

@login_required(login_url='app:login', redirect_field_name='home')
def admin_home(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'admin':
            current_month = date.today().month
            current_year = date.today().year
            unpayed = None

            all_students = 0
            teachers = Profile.objects.filter(company=profile.company, level='teacher', is_active=True).count()
            groups = Group.objects.filter(company=profile.company, status='1')
            accountants = Profile.objects.filter(
                company=profile.company, level='casher', is_active=True).count()
            for g in groups:
                all_students += g.students.count()

            all_groups = Group.objects.annotate(
                subscription_count=Count(
                    'subscription',
                    filter=Q(subscription__month__month=current_month) &
                    Q(subscription__month__year=current_year) &
                    Q(subscription__status='1')
                )
            ).filter(status='1').filter(company=profile.company)
            
            
            context = {
                'students':all_students,
                'teachers':teachers,
                'groups': groups.count(),
                'accountants':accountants,
                'items':all_groups
            }
            return render(request, 'admins/index.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')    

@login_required(login_url='app:login', redirect_field_name='home')
def admin_create_teacher(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'admin':
            subjects = Subject.objects.all()
            context = {'subjects': subjects}

            if request.method == "POST":
                try:
                    with atomic():
                        teacher_user = User.objects.create_user(
                            username=request.POST['phone'], password=request.POST['password'])
                        Profile.objects.create(
                            name=request.POST['name'],
                            phone=request.POST['phone'],
                            user=teacher_user,
                            level='teacher',
                            company=profile.company,
                            is_active=True
                        )
                        messages.success(request, "O'qituvchi ro'yxatga olindi")
                except:
                    messages.error(request, "Formada xatolik bor. Qaytadan urining", extra_tags='danger')

                return redirect('app:admin-home')

            return render(request, "admins/teacher.html", context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')


@login_required(login_url='app:login', redirect_field_name='home')
def admin_create_accountant(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'admin':

            if request.method == "POST":
                try:
                    with atomic():
                        casher_user = User.objects.create_user(
                            username=request.POST['phone'], password=request.POST['password'])
                        Profile.objects.create(
                            name=request.POST['name'],
                            user=casher_user,
                            phone=request.POST['phone'],
                            level='casher',
                            company=profile.company,
                            is_active=True
                        )
                        messages.success(request, "Hisobchi ro'yxatga olindi")
                except:
                    messages.error(
                        request, "Formada xatolik bor. Qaytadan urining", extra_tags='danger')

                return redirect('app:admin-home')

            return render(request, "admins/accountant.html")
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe') 

@login_required(login_url='app:login', redirect_field_name='home')
def admin_casher(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'admin':
            cashers = Profile.objects.filter(is_active=True, company=profile.company, level='casher')
            context = {'cashers':cashers}
            return render(request, "admins/cashers.html", context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

    

@login_required(login_url='app:login', redirect_field_name='home')
def edit_casher(request, pk,):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'admin':
            try:
                casher = Profile.objects.get(
                    id=pk, company=profile.company, level='casher')
                form = TeacherCreationForm(instance=casher)
            except:
                messages.error(request, "Xatolik, qaytadan urining",
                            extra_tags='danger')
                return redirect('app:admin-cashers')
            if request.method == "POST":
                with atomic():
                    form = TeacherCreationForm(request.POST, instance=casher)
                    if form.is_valid():
                        form.save()
                        messages.success(request, "O'zgartirish kiritildi")
                    else:
                        messages.error(
                            request, "Xatolik, formada xatolik bor", extra_tags='danger')
                    try:
                        casher_user = User.objects.get(
                            username=casher.user.username)
                        casher_user.username = request.POST['phone']
                        casher_user.save()
                    except:
                        messages.error(request, "Xatolik, ushbu raqamda foydalanuvchi mavjud", extra_tags='danger')

                return redirect(f'app:admin-cashers')

            context = {
                'form': form,
                'page_name': "Hisobchilar"
            }
            return render(request, 'data/form.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='home')
def delete_casher(request, pk):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher' or profile.level == 'admin':

            try:
                casher = Profile.objects.get(
                    id=pk, company=profile.company, level='casher')
            except:
                messages.error(request, "Xatolik, qaytadan urining",
                            extra_tags='danger')
                return redirect('app:admin-cashers')
            if request.method == "POST":
                casher_username = casher.user.username
                casher.delete()
                user = User.objects.get(username=casher_username)
                user.delete()
                messages.success(request, "Hisobchi o'chirildi")
                return redirect('app:admin-cashers')
            context = {
                'group': casher,
                'page_name': "Hisobchilar"
            }
            return render(request, 'data/delete.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='home')
def admin_settings(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'admin':
            company_settings = CompanySettings.objects.filter(company__id=profile.company.pk)
            if len(company_settings) == 0:
                company_settings = CompanySettings.objects.create(company=profile.company)
            else:
                company_settings = company_settings.first()

            context = {'settings':company_settings}
            if request.method == "POST":
                sets = CompanySettingsForm(instance=company_settings, data=request.POST)
                if sets.is_valid():
                    settings = sets.save(commit=False)
                    
                    if request.POST['attendace'] == 'true':
                        settings.attendace = True
                    else:
                        settings.attendace = False

                    if request.POST['payment'] == 'true':
                        settings.payment = True
                    else:
                        settings.payment = False

                    if request.POST['mark'] == 'true':
                        settings.mark = True
                    else:
                        settings.mark = False

                    settings.company=profile.company
                    settings.save()
                    messages.success(request, "Sozlamalar saqlandi")
                else:
                    messages.error(request, "Formada xatolik bor", extra_tags='danger')
                return redirect('app:admin-settings')
            return render(request, 'admins/settings.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')

@login_required(login_url='app:login', redirect_field_name='admin-home')
def admin_profile(request):
    profile = Profile.objects.get(user=request.user)
    if profile.level == 'admin':
        form = CustomPasswordChangeForm(user=request.user)
        if request.method == "POST":
            if request.POST['action'] == 'info':
                username = request.POST['username']
                fullname = request.POST['fullname']

                users = User.objects.filter(
                    username=username)
                if request.user.username != username and len(users) > 0:
                    messages.error(
                        request, "Siz kiritgan login boshqa foydalanuvchiga tegishli", extra_tags='danger')
                elif request.user.username != username:
                    user = User.objects.get(username=request.user.username)
                    user.username = username
                    user.save()
                    messages.success(request, "Login muvaffaqiyatli o'zgartirildi")

                profile = Profile.objects.get(user__username=username)
                profile.name = fullname
                profile.save()

                return redirect('app:admin-profile')
            elif request.POST['action'] == 'password':
                form = CustomPasswordChangeForm(user=request.user, data=request.POST)
                if form.is_valid():
                    user = form.save()
                    update_session_auth_hash(request, user)  # Important!
                    messages.success(
                        request, 'Parol muvaffaqiyatli o`zgartirildi!')
                    return redirect('app:admin-home')
            else:
                form = CustomPasswordChangeForm(user=request.user)


        return render(request, 'admins/profile.html', {'form': form})
    else:
        return redirect('app:login')


@login_required(login_url='app:login')
def teacher_home(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'teacher':

            groups = Group.objects.filter(status='1').filter(company=profile.company).filter(teacher=profile)
            context = {
                'groups': groups
            }
            return render(request, 'data/groups_list.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')


@login_required(login_url='app:login')
def delete_student(request, pk):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher':
            try:
                student = Student.objects.get(id=pk, company=profile.company, status='1')
                if request.method == "POST":
                    student.status = '0'
                    groups = student.group_set.all()
                    for group in groups:
                        group.students.remove(student)
                        group.save()
                    
                    subs = Subscription.objects.filter(student=student, company=profile.company)

                    for s in subs:
                        s.status = '0'
                        s.save()

                    student.save()
                    messages.success(request, "O'quvchi o'chirildi")
                    return redirect('app:datas')
            except:
                messages.error(request, "Xatolik, qaytadan urining", extra_tags='danger')
                return redirect("app:datas")
            context = {
                'group':student
            }
            return render(request, 'data/delete.html', context)

@login_required(login_url='app:login')
def casher_teachers(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher' or profile.level == 'admin':
            current_month = datetime.now().month

            teachers = Profile.objects.filter(is_active=True).filter(
                company=profile.company).filter(level='teacher').exclude(is_manager=True)
            
            for teacher in teachers:
                teacher.debt_balance = teacher.debt_amount(current_month)
                teacher.bonus_balance = teacher.bonus_amount(current_month)
                teacher.fine_balance = teacher.fine_amount(current_month)
                teacher.attendace_balance = teacher.attendace_amount(current_month)

            
            if 'month' in request.GET:
                try:
                    get_month = int(request.GET['month'])
                    current_month = int(get_month)
                    for teacher in teachers:
                        teacher.debt_balance = teacher.debt_amount(current_month)
                        teacher.bonus_balance = teacher.bonus_amount(current_month)
                        teacher.fine_balance = teacher.fine_amount(current_month)
                        teacher.attendace_balance = teacher.attendace_amount(current_month)
                    
                except:
                    pass

            if request.method == "POST":
                try:
                    teacher = Profile.objects.get(is_active=True, is_manager=False, level='teacher', company=profile.company, id=request.POST['teacher'])
                except:
                    messages.error(request, "Xatolik, o'qituvchi topilmadi.", extra_tags='danger')
                    return redirect('app:casher-teachers')
                
                if request.POST['balance'] == 'debt':   
                    try:
                        balance = TeacherDebt.objects.create(teacher=teacher, amount=abs(int(request.POST['amount'])), comment=request.POST['comment'])
                        messages.success(request, "Avans qo'shildi")
                    except:
                        messages.error(request, "Miqdor 0 dan katta bo'lishi kerak", extra_tags='danger')
                
                if request.POST['balance'] == 'fine':   
                    try:
                        balance = TeacherFine.objects.create(teacher=teacher, amount=abs(int(request.POST['amount'])), comment=request.POST['comment'])
                        messages.success(request, "Jarima qo'shildi")
                    except:
                        messages.error(request, "Miqdor 0 dan katta bo'lishi kerak", extra_tags='danger')
                    
                if request.POST['balance'] == 'bonus':   
                    try:
                        balance = TeacherBonus.objects.create(teacher=teacher, amount=abs(int(request.POST['amount'])), comment=request.POST['comment'])
                        messages.success(request, "Bonus qo'shildi")
                    except:
                        messages.error(request, "Miqdor 0 dan katta bo'lishi kerak", extra_tags='danger')
                
                return redirect('app:casher-teachers')

            context = {
                'teachers': teachers,
                'month': current_month
            }
            return render(request, 'data/teachers_list.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')
    

def casher_balance_history(request, pk):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher' or profile.level == 'admin':
            if 'type' in request.GET:
                if 'month' in request.GET:
                    current_month = int(request.GET['month'])
                else:
                    current_month = datetime.now().month
                current_year = datetime.now().year
                teacher = None
                try:
                    teacher = Profile.objects.get(id=pk, company=profile.company)
                except:
                    messages.error(request, "O'qituvchi topilmadi")
                    return redirect('app:casher-teacher')
                
                debt = TeacherDebt.objects.filter(teacher=teacher, date__month=current_month, date__year=current_year).order_by('-date')
                fine = TeacherFine.objects.filter(teacher=teacher, date__month=current_month, date__year=current_year).order_by('-date')
                bonus = TeacherBonus.objects.filter(teacher=teacher, date__month=current_month, date__year=current_year).order_by('-date')

                items = None


                if request.GET['type'] == 'debt':
                    items = debt
                
                elif request.GET['type'] == 'fine':
                    items = fine

                elif request.GET['type'] == 'bonus':
                    items = bonus

                else:
                    return redirect('app:casher-teachers')
                
                
                context = {
                    'teacher': teacher,
                    'items':items,
                    'type':request.GET['type']
                }
                return render(request, 'data/balance_history.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')
    

@login_required(login_url='app:login')
def expenses(request):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher' or profile.level == 'admin':
            current_month = datetime.now().month
            expenses = Expense.objects.filter(company=profile.company, date__month=current_month).order_by('-date')
            total = expenses.aggregate(Sum('amount'))
            if 'month' in request.GET:
                try:
                    current_month = int(request.GET['month'])
                except:
                    current_month = datetime.now().month

                expenses = Expense.objects.filter(company=profile.company, date__month = current_month).order_by('-date')
                total = expenses.aggregate(Sum('amount'))

            if request.method == "POST":
                try:
                    Expense.objects.create(amount=abs(int(request.POST['amount'])), comment=request.POST['comment'], company=profile.company)
                    messages.success(request, "Harajat kiritildi.")
                except:
                    messages.error(request, "Formada xatolik bor, qaytadan urining", extra_tags='danger')
                return redirect('app:expenses')
            context = {
                'items': expenses,
                'total': total['amount__sum']
            }
            return render(request, 'data/expenses.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')
        
        
@login_required(login_url='app:login')
def check_subscription(request, group, id, month):
    profile = Profile.objects.get(user=request.user)
    if check_sub(profile) == True or check_sub(profile) <= 5:
        if profile.level == 'casher' or profile.level == 'admin':
            try:
                student = Student.objects.get(id=id, company=profile.company)
                group = Group.objects.get(id=group, company=profile.company)
            except:
                messages.error(request, "Xatolik, talaba topilmadi")
                return redirect('app:datas')
            
            try:
                subs = Subscription.objects.filter(month__month=int(month), student=student, group=group)
            except:
                subs = None

            if request.method == "POST":
                with atomic():
                    try:
                        group = Group.objects.get(id=request.POST['group'])
                    except:
                        messages.error(request, 'Xatolik, guruh topilmadi')
                    year = datetime.now().year
                    months = datetime(year, int(month), 1, 12, 30, 0, tzinfo=UTC)

                    confirm_sub = Subscription.objects.create(
                        cost=int(request.POST['cost']),
                        month=months,
                        group=group,
                        student=student,
                        company=profile.company,
                        status='1'
                    )

                    confirm_sub.month = months
                    confirm_sub.save()

                    messages.success(request, "To'lov kiritildi")

                    return redirect(request.META.get('HTTP_REFERER'))                
            
            context = {
                'subs': subs,
                'student':student,
                'group':group
            }
            return render(request, 'data/check_sub.html', context)
        else:
            return redirect('app:login')
    else:
        return redirect('app:subscribe')
        
        
        

@login_required(login_url='app:login', redirect_field_name='home')
def check_teacher(request, pk):
    profile = Profile.objects.get(user=request.user)
    if profile.level == 'admin':
        teacher = None
        search = None
        groups = None
        students = 0
        attendace = None
        current_month = datetime.now().month
        current_year = datetime.now().year
        current_date = datetime.now()
        try:
            teacher = Profile.objects.get(id=pk, company=profile.company, is_active=True, level='teacher')
            groups = Group.objects.filter(status='1', company=teacher.company, teacher=teacher)
            for g in groups:
                students += g.students.all().count()
            attendace = TeacherAttendace.objects.filter(date__year=current_year, date__month=current_month, teacher=teacher).order_by('-id')
        except:
            messages.error(request, "O'qituvchi topilmadi", extra_tags='danger')
            return redirect('app:casher-teachers')
        
        if 'month' in request.GET:
            get_month = int(request.GET['month'])
            search = get_month
            attendace = TeacherAttendace.objects.filter(
                date__year=current_year, date__month=get_month, teacher=teacher).order_by('-id')
            date_time_str = f'18/{get_month}/{current_year} 01:55:19'
            current_date = datetime. strptime(date_time_str, '%d/%m/%Y %H:%M:%S')


        context = {
            'teacher': teacher, 
            'groups': groups,
            'students': students, 
            'attendace': attendace,
            'current_month': current_date,
            'search' : search
        }

        if request.method == "POST" and request.POST['actype'] == 'delete':
            for g in groups:
                g.teacher = None
                g.save()
            
            teacher.delete()
            messages.success(request, "O'qituvchi muvaffaqiyatli o'chirildi")
            return redirect('app:casher-teachers')

        return render(request, 'data/teacher.html', context)
    else:
        return redirect('app:login')


@login_required(login_url='app:login', redirect_field_name='home')
def group_subscription(request, pk):
    profile = Profile.objects.get(user=request.user)
    if profile.level == 'admin':
        current_month = datetime.now().month
        current_year = datetime.now().year
        try:
            group = Group.objects.get(id=pk)
        except:
            group:None
            messages.error(request, "Guruh topilmadi", extra_tags='danger')
            return redirect('app:casher-groups')
        
        subscriptions = Subscription.objects.filter(company=profile.company, group=group, month__month=current_month, month__year=current_year)
        if 'month' in request.GET:
            try:
                get_month = int(request.GET['month'])
                subscriptions = Subscription.objects.filter(
                    company=profile.company, group=group, month__month=get_month, month__year=current_year)

            except:
                subscriptions = Subscription.objects.filter(company=profile.company, group=group, month__month=current_month, month__year=current_year)
        

        context = {'subscriptions': subscriptions, 'group': group}
        return render(request, 'data/group_subscription.html', context)
    else:
        return redirect('app:login')




 
@login_required(login_url='app:login', redirect_field_name='home')
def template(request):
    profile = Profile.objects.get(user=request.user)
    if profile.level == 'admin':
        pass
    else:
        return redirect('app:login')

