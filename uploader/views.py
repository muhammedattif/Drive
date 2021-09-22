from django.shortcuts import render, redirect
from uploader.models import File

# Create your views here.

def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    files = File.objects.filter(uploader=request.user )

    context = {
    'files':files
    }
    return render(request, 'uploader/home.html', context)
