from django.shortcuts import render, redirect
from uploader.models import File
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required(login_url='login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    trashed_files = request.user.trash.files.all()
    files = File.objects.filter(uploader=request.user).exclude(pk__in=trashed_files)

    context = {
    'files':files
    }
    print(files.count())
    return render(request, 'uploader/home.html', context)

@login_required(login_url='login')
def upload(request):
    if request.method == 'POST':
        files_links = []
        user = request.user

        uploaded_files = request.FILES.getlist('file')

        for file in uploaded_files:

            file_name = file.name
            file_size = file.size
            file_category = get_file_cat(file)
            file_type = file.content_type
            file = File.objects.create(uploader=user, file_name=file_name, file_size=file_size, file_type=file_type, file_category=file_category, file=file)
            files_links.append(file.get_url())

        context = {
          'files_links': files_links
        }

        return render(request, 'uploader/upload.html', context)

    return render(request, 'uploader/upload.html')

@login_required(login_url='login')
def delete(request, id):
    context = {}
    try:
        file = File.objects.get(pk=id, uploader=request.user)
        file.delete()
        context['message'] = 'File Deleted Successfully!'
    except File.DoesNotExist:
        context['message'] = 'File Does not Exists!'

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



def get_file_cat(file):
    docs_ext =  ['pdf','doc','docx','xls','ppt','txt']
    if file.content_type.split('/')[0] == 'image':
        return 'images'
    elif file.content_type.split('/')[0] == 'audio' or file.content_type.split('/')[0] == 'video':
        return 'media'
    elif file.name.split('.')[-1] in docs_ext or file.content_type.split('/')[0] == 'text':
        return 'docs'
    else:
        return 'other'
