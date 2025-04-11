from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo_web.settings')
app = Celery('todo_web')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_schedule = {
    'send-email-notifications-every-minute': {
        'task': 'Todo_List_App.tasks.send_email_notifications',
        'schedule': 60.0,
    },
    'update-task-status-every-minute': {
        'task': 'Todo_List_App.tasks.update_task_status',
        'schedule': 60.0,
    },
}