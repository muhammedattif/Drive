from django.apps import AppConfig


class UploaderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'uploader'

    def ready(self):
        from uploader import receivers
