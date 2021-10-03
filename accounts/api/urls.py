from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from accounts.api.views import ObtainAuthTokenView
app_name = 'accounts'

urlpatterns = [
    # path('login', obtain_auth_token, name='login'),
    path('login', ObtainAuthTokenView.as_view(), name="login"),
  ]
