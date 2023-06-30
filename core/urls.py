from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('mydjangoadmin/', admin.site.urls),
    path('', include('app.urls')),
    path('manager/', include("manager.urls"))
]
