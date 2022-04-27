from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
from accounts.forms import CreateUserForm
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Q
# Create your views here.

# Registration View
@transaction.atomic # -> If there is an exception, the queries are rolled back.
def register_view(request):
    if not request.user.is_authenticated:
        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                response = {'status': True}
                return JsonResponse(json.dumps(response), content_type="application/json",safe=False)
            else:
                response = {'status': False}
                return JsonResponse(json.dumps(response), content_type="application/json",safe=False)

        return render(request, 'accounts/authenticate.html', context)
    return redirect('home')



# Login View
def login_view(request):
    if not request.user.is_authenticated:
        context = {}
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                response = {'status': True}
                return JsonResponse(json.dumps(response), content_type="application/json",safe=False)

            response = {'status': False}
            return JsonResponse(json.dumps(response), content_type="application/json",safe=False)

        return render(request, 'accounts/authenticate.html', context)
    return redirect('home')

# Logout View
def logout_view(request):
    logout(request)
    return redirect('login')


# Shared With Me Files
def shared_with_me(request):

    blocked_users = getattr(request.user, 'file_sharing_block_list', [])
    if blocked_users:
        blocked_users = blocked_users.users.values_list('id')

    files_shared_with_me = request.user.shared_with_me.prefetch_related('shared_by', 'shared_with', 'permissions', 'content_type', 'content_object').filter(\
    ~Q(shared_with__file_sharing_block_list__users__in=[request.user]),
    ~Q(shared_by__in=blocked_users),
    ~Q(shared_with__in=blocked_users),
    permissions__can_view=True,
    )

    context = {
    'files_shared_with_me': files_shared_with_me
    }

    return render(request, 'shared_with_me_content.html', context)
