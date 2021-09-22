from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from accounts.models import Account
from accounts.forms import CreateUserForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
# Create your views here.

def register(request):

    form = CreateUserForm()
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            messages.success(request, "Account was created for " + user)
            return redirect('')
    context = {
    'form': form
    }
    return render(request, 'accounts/register.html', context)



def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')

        messages.error(request, 'Invalid cradentials!')

    context = {
    }
    return render(request, 'accounts/login.html', context)

def logout(request):
    login(request)
    return redirect('login')
