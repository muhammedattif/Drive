# Standard library
import time
import uuid

# Django
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.utils import NestedObjects
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import Collector
from django.db.models.fields.related import ForeignKey
from django.db.utils import IntegrityError
from django.http import FileResponse
from django.shortcuts import redirect, render

# Files App
from file.models import File, SharedObject

# Folders App
from folder.models import Folder

# Local Django
from .forms import PrivacySettingsForm
from .models import CompressedFile, DriveSettings


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

from pathlib import Path


def recursive(folder):

    for file in folder.files.all():
        print(folder.get_folder_tree_as_dirs())
        print(file.file)
        base_dir = f'{settings.DRIVE_PATH}/{str(file.user.unique_id)}'

        new_path = f'{base_dir}/{folder.get_folder_tree_as_dirs()}/{file.name}'
        print(new_path)
    for folder in folder.sub_folders.all():
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

        request.user.folders.all().delete()
        request.user.files.all().delete()
        messages.error(request, 'Account data has been erased.')

    return redirect('home')


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

def shared_with_me_detail(request, sharing_id):

    shared_object = SharedObject.objects.prefetch_related('permissions').filter(id=sharing_id, content_type=ContentType.objects.get(model='folder')).first()

    if not (shared_object and request.user.can_share_with(shared_object.shared_by)):
        return redirect('error')


    context = {
        'folder': shared_object.content_object,
        'shared_object': shared_object,
        'files': shared_object.content_object.files.all(),
        'folders': shared_object.content_object.sub_folders.all()
    }

    return render(request, 'shared_content.html', context)
