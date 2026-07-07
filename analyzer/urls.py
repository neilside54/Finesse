from django.urls import path
from analyzer.views import (
    ChessAnalyzeView, ChessAsyncAnalyzeView,
    TaskStatusView, InputOptionsView,
    SaveAnalysisView, SavedAnalysesView, SavedAnalysisDetailView,
)

urlpatterns = [

    # Synchronous route
    path('analyze/', ChessAnalyzeView.as_view(), name='chess-analyze'),

    # Async routes (Celery)
    path('analyze-async/', ChessAsyncAnalyzeView.as_view(), name='chess-analyze-async'),
    path('task/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
    path('input-options/', InputOptionsView.as_view(), name='input-options'),

    # Saved analyses
    path('saved-analyses/save/', SaveAnalysisView.as_view(), name='save-analysis'),
    path('saved-analyses/', SavedAnalysesView.as_view(), name='saved-analyses'),
    path('saved-analyses/<int:analysis_id>/', SavedAnalysisDetailView.as_view(), name='saved-analysis-detail'),
]