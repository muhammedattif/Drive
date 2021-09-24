from django.shortcuts import render, redirect
from uploader.models import File
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required(login_url='login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    files = File.objects.filter(uploader=request.user)

    context = {
    'files':files
    }
    return render(request, 'uploader/home.html', context)

@login_required(login_url='login')
def upload(request):
    if request.method == 'POST':
        user = request.user

        uploaded_file = request.FILES['file']
        file_size = uploaded_file.size
        file = File.objects.create(uploader=user, file_name=uploaded_file.name, file_size=file_size, file=uploaded_file)

        context = {
          'file': file
        }

        return render(request, 'uploader/upload.html', context)

    return render(request, 'uploader/upload.html')

@login_required(login_url='login')
def delete(request, id):
    context = {}

    if request.method == 'POST':
        try:
            file = File.objects.get(pk=id, uploader=request.user)
            file.delete()
            context['message'] = 'File Deleted Successfully!'
        except File.DoesNotExist:
            context['message'] = 'File Does not Exists!'
    else:
        context['message'] = 'Method not Allowed!'

    return render(request, 'uploader/home.html', context)


@login_required(login_url='login')
def filter(request, cat):
    context = {}
    if cat == 'all':
        files = request.user.files.all()
    else:
        files = File.objects.filter(uploader=request.user, file_category = cat)

    context['files'] = files
    return render(request, 'uploader/home.html', context)
