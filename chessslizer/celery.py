import os
from celery import Celery

# Устанавливаем дефолтные настройки Django для celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chessslizer.settings')

app = Celery('chessslizer')

# Читаем конфиг из settings.py с префиксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически ищем таски (tasks.py) во всех приложениях
app.autodiscover_tasks()