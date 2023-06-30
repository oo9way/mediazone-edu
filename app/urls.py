from .views import (
    home, login_page, logout_page,
    datas, group, create_group, edit_group, delete_group,
    teachers, create_teacher, edit_teacher, delete_teacher,
    create_student, print_group, daily_history, groups_list,
    send_message, user_settings, change_password, get_cheque,
    admin_home, admin_create_teacher, admin_create_accountant,
    admin_casher, edit_casher, delete_casher, admin_settings,
    admin_profile, teacher_home, subscibe_page, casher_teachers,
    casher_balance_history, expenses, delete_student, edit_student,
    check_subscription, 
    check_teacher, group_subscription
)
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

app_name = 'app'

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_page, name='login'),
    path('subscribe/', subscibe_page, name='subscribe'),
    path('logout/', logout_page, name='logout'),


    path('data/', datas, name='datas'),
    path('data/create-group/', create_group, name='create-group'),
    path('data/group/<int:pk>', group, name='group'),
    path('data/print-group/<int:pk>', print_group, name='print-group'),
    path('data/table', daily_history, name='history'),
    path('data/cheque/<int:pk>', get_cheque, name='get-cheque'),
    path('data/teachers', casher_teachers, name='casher-teachers'),
    path('data/teachers/balance/<int:pk>', casher_balance_history, name='casher-teacher-history'),
    path('data/expenses', expenses, name='expenses'),



    path('data/edit-group/<int:pk>', edit_group, name='edit-group'),
    path('data/delete-group/<int:pk>', delete_group, name='delete-group'),
    path('data/delete-student/<int:pk>', delete_student, name='delete-student'),

    path('teachers/', teachers, name='teachers'),
    path('teachers/create-teacher/', create_teacher, name='create-teacher'),
    path('teachers/edit-teacher/<int:pk>', edit_teacher, name='edit-teacher'),
    path('teachers/delete-teacher/<int:pk>', delete_teacher, name='delete-teacher'),

    path('messages/groups', groups_list, name='message-groups'),
    path('messages/send/<int:pk>', send_message, name='send-message'),

    path('user/settings', user_settings, name='settings'),
    path('user/change-password', change_password, name='change-password'),

    path('students/create-student/', create_student, name='create-student'),
    path('students/edit-student/<int:pk>', edit_student, name='edit-student'),


    path('admins/', admin_home, name='admin-home'),
    path('admins/create-teacher', admin_create_teacher,
         name='admin-create-teacher'),
    path('admins/create-accountant', admin_create_accountant,
         name='admin-create-accountant'),

    path('admins/cashers', admin_casher, name='admin-cashers'),
    path('admins/edit-casher/<int:pk>', edit_casher, name='admin-edit-casher'),
    path('admins/delete-casher/<int:pk>',
         delete_casher, name='admin-delete-casher'),

    path('admins/settings', admin_settings, name='admin-settings'),
    path('admins/profile', admin_profile, name='admin-profile'),
    path('teacher/', teacher_home, name='teacher-home'),
    path('subscription/history/<int:group>/<int:id>/<int:month>', check_subscription, name='check-subscription'),
    
    
    path('data/group/subscription/<int:pk>', group_subscription, name='group-subscription'),
    path('data/teachers/<int:pk>', check_teacher, name='check-teacher'),



]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
