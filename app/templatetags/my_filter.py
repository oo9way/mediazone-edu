from django import template
from app.models import Subscription, Group
from django.db.models import Sum
from datetime import datetime

register = template.Library()


@register.filter(name='absolute')
def absolute(value):
    value = int(value)
    return abs(value)

@register.filter(name='gs')
def get_salary(value, mode):
    current_month = datetime.now().month
    current_year = datetime.now().year
    group = Group.objects.get(id=value)
    if mode == 'current':
        subscriptions = Subscription.objects.filter(
            group=group, month__month=current_month, month__year=current_year, status='1').aggregate(Sum('cost'))
    else:
        subscriptions = Subscription.objects.filter(
            group=group, month__month=int(mode), month__year=current_year, status='1').aggregate(Sum('cost'))
    if subscriptions['cost__sum']:
        return subscriptions['cost__sum']
    return 0