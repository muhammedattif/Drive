# Django
from django.urls import path

# Accounts App
from accounts.views import login_view, register_view

app_name = 'accounts'

urlpatterns = [
    path('', login_view, name='login'),
    path('register', register_view, name='register')
  ]
