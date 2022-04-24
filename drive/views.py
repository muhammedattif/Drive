from django.shortcuts import render, redirect, reverse
from file.models import File
from folder.models import Folder
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from accounts.models import Account
from .models import DriveSettings, CompressedFile
from .forms import PrivacySettingsForm
from django.contrib import messages
from django.http import HttpResponse, FileResponse
import time
import uuid
from django.contrib.admin.utils import NestedObjects
from activity.models import Activity

from django.db.models.deletion import Collector
from django.db.models.fields.related import ForeignKey

from django.db.utils import IntegrityError


class ObjectCloner(object):
    """
    [1]. The simple way with global configuration:
    >>> cloner = ObjectCloner()
    >>> cloner.set_objects = [obj1, obj2]   # or can be queryset
    >>> cloner.include_childs = True
    >>> cloner.max_clones = 1
    >>> cloner.execute()

    [2]. Clone the objects with custom configuration per-each objects.
    >>> cloner = ObjectCloner()
    >>> cloner.set_objects = [
        {
            'object': obj1,
            'include_childs': True,
            'max_clones': 2
        },
        {
            'object': obj2,
            'include_childs': False,
            'max_clones': 1
        }
    ]
    >>> cloner.execute()
    """
    set_objects = []            # list/queryset of objects to clone.
    include_childs = True       # include all their childs or not.
    max_clones = 1              # maximum clone per-objects.

    def clone_object(self, object):
        """
        function to clone the object.
        :param `object` is an object to clone, e.g: <Post: object(1)>
        :return new object.
        """
        try:
            object.pk = None
            object.unique_id = uuid.uuid4()
            object.save()
            return object
        except IntegrityError:
            return None

    def clone_childs(self, object):
        """
        function to clone all childs of current `object`.
        :param `object` is a cloned parent object, e.g: <Post: object(1)>
        :return
        """
        # bypass the none object.
        if object is None:
            return

        # find the related objects contains with this current object.
        # e.g: (<ManyToOneRel: app.comment>,)
        related_objects = object._meta.related_objects

        if len(related_objects) > 0:
            for relation in related_objects:
                # find the related field name in the child object, e.g: 'post'
                remote_field_name = relation.remote_field.name

                # find all childs who have the same parent.
                # e.g: childs = Comment.objects.filter(post=object)
                childs = relation.related_model.objects.all()

                for old_child in childs:
                    new_child = self.clone_object(old_child)

                    if new_child is not None:
                        # "TypeError: Direct assignment to the forward side of a many-to-many set is prohibited. Use comments.set() instead."
                        # how can I clone that M2M values?
                        setattr(new_child, remote_field_name, object)
                        new_child.save()

                    self.clone_childs(new_child)
        return

    def execute(self):
        include_childs = self.include_childs
        max_clones = self.max_clones
        new_objects = []

        for old_object in self.set_objects:
            # custom per-each objects by using dict {}.
            if isinstance(old_object, dict):
                include_childs = old_object.get('include_childs', True)
                max_clones = old_object.get('max_clones', 1)
                old_object = old_object.get('object')  # assigned as object or None.

            for _ in range(max_clones):
                new_object = self.clone_object(old_object)
                print(new_object)
                if new_object is not None:
                    if include_childs:
                        self.clone_childs(new_object)
                    new_objects.append(new_object)

        return new_objects

# Home Page View
@login_required(login_url='login')
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')

    # Get files of home dir if exist
    try:
        files = File.objects.filter(user=request.user, trash=None, parent_folder=None).select_related('privacy')
    except Exception:
        files = File.objects.filter(user=request.user).select_related('privacy')

    # Get folders of home dir if exist
    try:
        folders = Folder.objects.filter(parent_folder=None, user=request.user)
    except Exception as e:
        print(e)
        folders = None

    paginator = Paginator(files, 10)  # Show 10 files per page.
    page_number = request.GET.get('page')
    files = paginator.get_page(page_number)

    context = {
        'files': files,
        'folders': folders
    }

    return render(request, 'drive/home.html', context)


def recursive(folder):

    for file in folder.files.all():
        files_obj.append(file)
    for folder in folder.sub_folders.all():
        folders_obj.append(folder)
        recursive(folder)

# Filter files based on category view
@login_required(login_url='login')
def filter(request, cat):
    """
    This function is to filter files based on category
    """
    context = {}
    files = None
    if cat == 'all':
        files = File.objects.filter(user=request.user, trash=None, parent_folder=None).select_related('privacy')

    elif cat == 'folders':
        try:
            folders = Folder.objects.filter(parent_folder=None, user=request.user)
        except Exception:
            folders = None
        context['folders'] = folders
    else:
        files = File.objects.filter(user=request.user, category=cat, trash=None, parent_folder=None).select_related('privacy')

    if files:
        paginator = Paginator(files, 10)  # Show 10 files per page.
        page_number = request.GET.get('page')
        files = paginator.get_page(page_number)
        context['files'] = files

    return render(request, 'drive/home.html', context)

# privacy settings view
@login_required(login_url='login')
def privacy_settings(request):

    try:
        privacy_settings = DriveSettings.objects.get(user=request.user)
    except DriveSettings.DoesNotExist:
        return redirect('error')

    if request.method == 'POST':
        print(request.POST)
        form = PrivacySettingsForm(request.POST, instance=privacy_settings)

        if form.is_valid():
            form.save()
            messages.success(request,'File permissions updated successfully')
        else:
            messages.error(request,
                            'Something went wrong. Try again later!.')

    context = {
        'form': PrivacySettingsForm(instance=privacy_settings),
        'default_upload_privacy': privacy_settings.default_upload_privacy
    }

    return render(request, 'drive/privacy_settings.html', context)

@login_required(login_url='login')
@permission_required('drive.can_compress_account_data', raise_exception=True)
def compress_user_files(request):

    from .tasks import async_compress_user_files
    compressed_data, created = CompressedFile.objects.get_or_create(user=request.user)
    if not created:
        compressed_data.is_downloaded = False
        compressed_data.save(update_fields=['is_downloaded'])
    async_compress_user_files.delay(request.user.id, compressed_data.id)
    time.sleep(1)

    messages.success(request, 'Your data is being compressed now, and will be available soon.')

    return redirect('home')

@login_required(login_url='login')
@permission_required('drive.can_compress_account_data', raise_exception=True)
def download_compressed_data(request):

    compressed_data = CompressedFile.objects.get(user=request.user)
    if compressed_data:
        compressed_data.is_downloaded = True
        compressed_data.save(update_fields=['is_downloaded'])
        response = FileResponse(compressed_data.zip, as_attachment=True)
        response['Content-Disposition'] = 'attachment; filename={}'.format(request.user.username + '.zip')
        return response

@login_required(login_url='login')
@permission_required('drive.can_erase_account_data', raise_exception=True)
def erase_account_data(request):
    if request.method == 'POST':
        request.user.files.all().delete()
        request.user.folders.all().delete()
        messages.error(request, 'Account data has been erased.')

    return redirect('home')
