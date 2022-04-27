from django.urls import path
from accounts.views import login_view, register_view, shared_with_me

app_name = 'accounts'

urlpatterns = [
    path('', login_view, name='login'),
    path('register', register_view, name='register'),
    path('shared-with-me', shared_with_me, name='shared-with-me')
  ]
