from django.apps import AppConfig


class InteriorNotificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interior_notification'

    def ready(self):
        import interior_notification.reciver
# myapp/apps.py