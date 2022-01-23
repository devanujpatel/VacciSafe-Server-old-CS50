from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('log_in/', views.log_in, name='log_in'),
    path('update_appt_records/', views.update_appt, name='update_appt_records'),
]