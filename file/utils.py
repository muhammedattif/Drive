from django.conf import settings

# Imports for image compression
from PIL import Image
from io import BytesIO
import sys
from django.core.files.uploadedfile import InMemoryUploadedFile

# imports for generating random link
import random
from string import digits, ascii_uppercase, ascii_lowercase


# this function is for image compression
def compress_image(image, image_type):
    # Open the image and Convert it to RGB color mode
    image_temporary = Image.open(image)
    image_format = image_temporary.format
    print(image_format)

    # save image to BytesIO object
    output_io_stream = BytesIO()
    # save image to BytesIO object
    image_temporary.save(output_io_stream, format=image_format, optimize=True)
    output_io_stream.seek(0)
    image = InMemoryUploadedFile(output_io_stream, 'ImageField',
                                 "{}.{}".format(image.name.split('.')[0:-1], image.name.split('.')[-1]), image_type,
                                 sys.getsizeof(output_io_stream), None)
    return image


# This function is for generating a random combines int and string for file links
legals = digits + ascii_lowercase + ascii_uppercase


def rand_link(length, char_set=legals):
    link = ''
    for _ in range(length): link += random.choice(char_set)
    return link


def generate_file_link(file_name):
    link = rand_link(40)
    # Add random string to filename
    ext = file_name.rsplit('.', 1)[1]
    link = link + '.' + ext
    return link


# this function is for initializing file path
def get_file_path(self, filename):
    # # Get current date
    # date = datetime.now()
    # year = str(date.strftime('%Y'))
    # month = str(date.strftime('%m'))
    # day = str(date.strftime('%d'))

    # # Add random string to filename
    # name = filename.rsplit('.', 1)[0]
    # ext = filename.rsplit('.', 1)[1]
    # random_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    # filename = name + '_' + random_text + '.' + ext

    # Get folder tree to save
    if self.parent_folder:
        folder_tree = self.parent_folder.get_folder_tree_as_dirs()
        return f'{settings.DRIVE_PATH}/{str(self.uploader.unique_id)}/{folder_tree}/{filename}'

    return f'{settings.DRIVE_PATH}/{str(self.uploader.unique_id)}/{filename}'


# Function for categorising files
def get_file_cat(file):
    docs_ext = ['pdf', 'doc', 'docx', 'xls', 'ppt', 'txt']
    try:
        if file.content_type.split('/')[0] == 'image':
            return 'images'
        elif file.content_type.split('/')[0] == 'audio' or file.content_type.split('/')[0] == 'video':
            return 'media'
        elif file.name.split('.')[-1] in docs_ext or file.content_type.split('/')[0] == 'text':
            return 'docs'
        else:
            return 'other'
    except Exception as e:
        return 'other'
