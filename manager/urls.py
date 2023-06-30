from django.urls import path
from .views import companies, create_company, subscriptions, change_password


app_name = 'manager'

urlpatterns = [
    path("", companies, name='companies'),
    path("create/", create_company, name='create-company'),
    path('subscriptions/', subscriptions, name='subscriptions'),
    path('settings/', change_password, name='settings'),

]