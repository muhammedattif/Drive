from django.conf import settings

# Imports for image compression
from PIL import Image
from io import BytesIO
import sys
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files import File

# imports for generating random link
import random
from string import digits, ascii_uppercase, ascii_lowercase
import subprocess
from pathlib import Path
import cv2

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
    # Get folder tree to save
    if self.parent_folder:
        folder_tree = self.parent_folder.get_folder_tree_as_dirs()
        return f'{settings.DRIVE_PATH}/{str(self.user.unique_id)}/{folder_tree}/{filename}'

    return f'{settings.DRIVE_PATH}/{str(self.user.unique_id)}/{filename}'

def get_video_cover_path(self, filename):

    media_file_path = Path(self.media_file.file.url)
    media_file_name = media_file_path.stem
    cover_extension = Path(filename).suffix
    folder_tree = Path(settings.DRIVE_PATH).joinpath(str(self.media_file.user.unique_id)).joinpath(self.media_file.parent_folder.get_folder_tree_as_dirs())
    video_cover_path = folder_tree.joinpath(f'{media_file_name}_cover{cover_extension}')

    return video_cover_path


def get_video_subtitle_path(self, filename):
    media_file_path = Path(self.media_file.media_file.file.url)
    media_file_name = media_file_path.stem
    subtitle_extension = Path(filename).suffix
    folder_tree = Path(settings.DRIVE_PATH).joinpath(str(self.media_file.media_file.user.unique_id)).joinpath(
        self.media_file.media_file.parent_folder.get_folder_tree_as_dirs())
    video_cover_path = folder_tree.joinpath(f'{media_file_name}_{self.language}_subtitle{subtitle_extension}')

    return video_cover_path


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

def convert_video_quality(video_path, quality):
    found, width, height = get_resolution(quality)
    if not found:
        return None, None, False

    video_name = Path(video_path)
    new_video_path = Path(video_path).parent.joinpath(f'{video_name.stem}_{quality}{video_name.suffix}')

    # old Command
    # cmd = ['ffmpeg', '-y', '-i', video_path, '-filter_complex', f'[0]scale=-1:width={width}:height={height}[s0]',
    #        '-map', '[s0]', '-map', '0:a', '-c:a', 'copy', new_video_path]

    cmd = f"ffmpeg -y -i '{video_path}' -vf scale=-1:width={width}:height={height} '{new_video_path}'"
    subprocess.call(
        cmd,
        shell=True
    )

    new_video = File(open(new_video_path, 'rb'))
    new_video_path = shorten_path(new_video_path)
    return new_video, new_video_path, True


def shorten_path(file_path):
    return Path(*Path(file_path).parts[5:])

def get_resolution(quality):
    if quality == '144p':
        return True, 176, 144
    elif quality == '240p':
        return True,426, 240
    elif quality == '360p':
        return True,480, 360
    elif quality == '480p':
        return True,640, 480
    elif quality == '720p':
        return True,1280, 720
    elif quality == '1080p':
        return True,1920, 1080
    return False, 0, 0

def detect_quality(path):
    vid = cv2.VideoCapture(path)
    height = vid.get(cv2.CAP_PROP_FRAME_HEIGHT)
    width = vid.get(cv2.CAP_PROP_FRAME_WIDTH)
    return str(int(height)) + 'p'

def get_supported_qualities(quality):

    qualities = ['144p', '240p', '360p', '480p', '720p', '1080p']
    if quality not in qualities:
        return []

    quality_index = qualities.index(quality)
    supported_qualities = qualities[:quality_index]
    return supported_qualities
