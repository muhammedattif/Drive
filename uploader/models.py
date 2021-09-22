from django.db import models
from django.conf import settings
from datetime import datetime
from django.contrib.sites.models import Site
# Create your models here.

User = settings.AUTH_USER_MODEL

def get_file_path(self, filename):
    date = datetime.now()
    year = str(date.strftime('%Y'))
    month = str(date.strftime('%m'))
    return f'{self.uploader.username}/{year}/{month}/{filename}'

class File(models.Model):

    uploader = models.ForeignKey(User, on_delete=models.CASCADE, related_name = "files")
    file = models.FileField(upload_to=get_file_path)
    uploaded_at = models.DateTimeField(verbose_name="Date Uploaded", auto_now_add=True)

    def __str__(self):
        return self.file.name

    def get_url(self):
        return 'http://%s%s' % (Site.objects.get_current().domain, self.file.url)
