from datetime import datetime, timedelta
from app.models import CompanySubscription, Profile

def check_sub(profile):
    today = datetime.today()
    first_day_of_month = datetime(today.year, today.month, 1)
    days_since_first_day = (today - first_day_of_month).days
    current_month = datetime.now().month
    current_year = datetime.now().year
    subsciption = CompanySubscription.objects.filter(company=profile.company).filter(
        date__month=current_month, date__year=current_year)

    if len(subsciption) == 1:
        return True
    else:
        return days_since_first_day

def subscription(request):
    if request.user.is_authenticated and request.user.is_staff == False:
        return {
            'active_days': check_sub(request.user.profile_set.first()),
            'manager':Profile.objects.filter(is_manager=True).first()
        }
    return {
        'active_days':0
    }
