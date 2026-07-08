from django.urls import path

from accounts.views import (
    AuthStatusView,
    LinkedAccountsView,
    LinkedAccountDetailView,
    UsernameCheckView,
)

urlpatterns = [
    path("auth/status/", AuthStatusView.as_view(), name="auth-status"),
    path("auth/username-check/<str:username>/", UsernameCheckView.as_view(), name="username-check"),
    path("auth/linked-accounts/", LinkedAccountsView.as_view(), name="linked-accounts"),
    path(
        "auth/linked-accounts/<uuid:account_id>/",
        LinkedAccountDetailView.as_view(),
        name="linked-account-detail",
    ),
]
