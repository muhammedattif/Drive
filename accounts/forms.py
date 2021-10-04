from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth import get_user_model
from accounts.models import Account

# This is a User Registration form ModelForm
class CreateUserForm(UserCreationForm):
    email = forms.EmailField(max_length=255, help_text="Required. Add a valid Email Address.")
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())


    class Meta:

        model = Account
        fields = ('email', 'username', 'job_title', 'password1', 'password2')
