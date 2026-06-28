from django.urls import path
from analyzer.views import ChessAnalyzeView, ChessAsyncAnalyzeView, TaskStatusView

urlpatterns = [
    # Синхронный роут
    path('analyze/', ChessAnalyzeView.as_view(), name='chess-analyze'),

    # Асинхронные роуты (Celery)
    path('analyze-async/', ChessAsyncAnalyzeView.as_view(), name='chess-analyze-async'),
    path('task/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
]