from __future__ import annotations

import re
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

if TYPE_CHECKING:
    from django.http import HttpRequest
    from allauth.socialaccount.models import SocialLogin


class ChesslizerSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter that auto-generates unique usernames during social signup.

    Google OAuth provides email and name but not a system username,
    which would cause allauth to show an unstyled signup form. This
    adapter generates a username from the email prefix and ensures it
    is unique, letting the OAuth flow complete without intermediate pages.
    """

    def save_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        form=None,
    ):
        """Save the user, auto-generating a username if none was provided."""
        user = sociallogin.user

        # If the user has no username and auto-signup is happening
        # (form is None), generate one from email or name.
        if form is None and not user.username:
            user.username = self._generate_unique_username(sociallogin)

        return super().save_user(request, sociallogin, form=form)

    def _generate_unique_username(self, sociallogin: SocialLogin) -> str:
        """Generate a unique username from the social account data."""
        user = sociallogin.user
        email = user.email or ""

        # Try email prefix first
        if email and "@" in email:
            base = email.split("@")[0].lower()
        else:
            # Fallback: use the provider name and a timestamp hash
            provider_id = sociallogin.account.provider if sociallogin.account else "user"
            base = provider_id[:20]

        # Clean the base: only keep safe characters
        base = re.sub(r"[^a-z0-9_]", "_", base)[:28].strip("_")
        if not base or len(base) < 2:
            base = "user"

        # Ensure uniqueness
        User = get_user_model()
        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            suffix = str(counter)
            max_len = 30 - len(suffix) - 1
            username = f"{base[:max_len]}_{suffix}"
            counter += 1

        return username
