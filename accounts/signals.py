from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver

from accounts.models import LinkedChessAccount


@receiver(social_account_added)
def link_social_account(sender, request, sociallogin, **kwargs):
    """Auto-link a chess platform account when the user signs in via OAuth.

    When a user registers or signs in via Lichess or Chess.com, this signal
    handler creates a LinkedChessAccount entry so the account appears in
    the user's profile without requiring them to manually add it.
    """
    provider = sociallogin.account.provider  # "lichess" or "google"

    # Map allauth provider names to our platform choices
    PLATFORM_MAP = {
        "chess.com": "chess.com",
        "lichess": "lichess",
    }

    platform = PLATFORM_MAP.get(provider)
    if not platform:
        return  # Not a chess platform — nothing to link

    # The username on the chess platform
    extra_data = sociallogin.account.extra_data
    # allauth stores Lichess username under "id", Chess.com under "username"
    platform_username = (
        extra_data.get("username")
        or extra_data.get("id")
        or extra_data.get("login")
    )
    if not platform_username:
        return  # No username available

    # Avoid duplicates
    LinkedChessAccount.objects.get_or_create(
        user=sociallogin.user,
        platform=platform,
        platform_username=platform_username,
        defaults={"is_primary": True},  # First linked account is primary by default
    )
