
# Description
Drive is a file storage service, Drive allows users to store files in the cloud, manage file permissions, and share files.

# 𝗧𝗲𝗰𝗵𝗻𝗼𝗹𝗼𝗴𝗶𝗲𝘀
- Python/Django
- Django Template
- Django Rest Framework
- PostgreSQL
- Celery
- Redis

# 𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀
- SignIn/Signup/SignOut

- Upload Files

- Files Links Privacy (Private, Public, Accessed only by specific users)

- Files Classification (Images, Docs, Media, etc..)

- Move Files into Trash (Erased after 30 days Automatically)

- Recover Files from Trash

- Permanently Delete Files

- Rename File

- Download File

- Detect Media Files Quality and Suggest Lower Qualities to Convert to (1080p, 720p, etc..)

- File Details (Type, Size, Category, Location, Uploaded at)

- Create Folders

- Rename Folders

- Download Folders as a Zip File(Recursively downloads all its childs)

- Delete Folder

- Copy/Paste (Folders/Files)

- Cut/Paste (Folders/Files)

- Shared Files (You can share Files/Folders with anyone and add permissions on it) (It will appear in the other user’s profile)

- Shared Files Permissions (Can view, Can Delete, Can Download, Can Change)
* It followes the General Action permissions for the user who shared the File/Folder.

- Block users from sharing Files with me

- Compress all the Profile’s data as a Zip File

- Erase all Profile’s Data

- Uploading Settings (Limited/Unlimited storage IN GB)

- Default Upload File’s Privacy (Private/Public)

All the previous actions are restricted to a permissions, so the user must have the permission of the action to perform it.

For Example: If the user doesn’t have a permission to Copy/Paste Folders, the action will not appear and if he play tricks on the system, the API view that is responsible for performing this action will reject its request returning Http 403 (Forbidden)

# Media Directory

All media files saved in /media in the base directory (Don't serve it with Nginx)


# Steps


## 1- Install the requirements

```bash
pip install -r requirements.txt
```

## 2- Apply migrations

```bash
python manage.py migrate
```

## 3- Create Super User

```bash
python manage.py createsuperuser
```

## 4- Update Settings Configurations

Configure Redis server, port, and DB Settings

## 5- Start Celery Worker

Run this command in the project's main directory
```
celery -A cloud worker -l info
```
