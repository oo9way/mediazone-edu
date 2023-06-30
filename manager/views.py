from django.shortcuts import render, redirect
from app.models import Company, CompanySubscription, Profile
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.db.transaction import atomic
from django.db.models import Q, Count
from datetime import date
from django.contrib.auth.decorators import login_required

from django.contrib import messages
# Create your views here.


@login_required(login_url='app:login')
def companies(request):
    profile = Profile.objects.get(user=request.user)
    if profile.is_manager:
        current_date = date.today()
        current_month = date.today().month
        current_year = date.today().year
        companies = Company.objects.all().annotate(
            subscriptions_this_month=Count('companysubscription', filter=Q(
                companysubscription__date__month=current_month, companysubscription__date__year=current_year))
        )

        s_count = 0
        for c in companies:
            s_count += c.subscriptions_this_month

        s_count = companies.count() - s_count

        if request.method == "POST":
            try:
                company = Company.objects.get(id=request.POST['company_id'])
            except:
                messages.error(request, "Xatolik, kompaniya topilmadi")
                return redirect('manager:companies')

            if request.POST['action'] == 'subscribe':
                try:
                    cost = int(request.POST['cost'])
                except:
                    messages.error(request, "Xatolik, summa noto'g'ri kiritildi")
                    return redirect('manager:companies')

                CompanySubscription.objects.create(
                    company=company,
                    cost=cost
                )

                messages.success(request, "Muvaffaqiyatli aktivlashtirildi")
                return redirect("manager:companies")

            elif request.POST['action'] == 'unsubscribe':
                try:
                    subscription = CompanySubscription.objects.filter(company=company).filter(
                        date__month=current_month, date__year=current_year)
                    s = subscription.first()
                    s.delete()
                    messages.success(request, "Obuna bekor qilindi")

                except:
                    messages.error(request, "Obuna topulmadi")

                return redirect('manager:companies')

        context = {
            'companies': companies,
            'date': current_date,
            's_count': s_count

        }
        return render(request, 'manager/companies.html', context)
    else:
        return redirect('app:login')


@login_required(login_url='app:login')
def create_company(request):
    profile = Profile.objects.get(user=request.user)
    if profile.is_manager:
        if request.method == 'POST':
            try:
                with atomic():
                    user = User.objects.create_user(
                        username=request.POST['username'], password=request.POST['password'])
                    company = Company.objects.create(
                        name=request.POST['company_name'],
                        phone=request.POST['phone'],
                        cost=request.POST['cost'],
                        owner=request.POST['owner_name']
                    )

                    profile = Profile.objects.create(
                        name=request.POST['company_name'],
                        user=user,
                        phone=request.POST['phone'],
                        level='admin',
                        company=company,
                        is_active=True,
                    )
                messages.success(request, "Abonent muvaffaqiyatli qo'shildi")
            except:
                messages.error(request, "Formada xatolik bor, login oldin olingan bo'lishi mumkin", extra_tags='danger')
            return redirect("manager:companies")

        return render(request, 'manager/createcompany.html')
    else:
        return redirect('app:login')


@login_required(login_url='app:login')
def subscriptions(request):
    profile = Profile.objects.get(user=request.user)
    if profile.is_manager:
        items = CompanySubscription.objects.all().order_by('-date')
        context = {'items':items}
        return render(request, 'manager/subscriptions.html', context)
    else:
        return redirect('app:login')


@login_required(login_url='app:login')
def change_password(request):
    profile = Profile.objects.get(user=request.user)
    if profile.is_manager:
        if request.method == 'POST':
            form = PasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(
                    request, 'Parol muvaffaqiyatli o`zgartirildi.')
            return redirect('manager:settings')
        return render(request, 'manager/settings.html')
    else:
        return redirect('app:login')
