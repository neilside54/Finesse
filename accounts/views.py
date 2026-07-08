import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django_ratelimit.decorators import ratelimit

from accounts.models import LinkedChessAccount


# ── CSRF / auth status ─────────────────────────────────────────────


@method_decorator(ensure_csrf_cookie, name="get")
class AuthStatusView(View):
    """Return the current user's auth state so the SPA knows whether
    to show login/register or a profile dropdown.

    Also sets the ``csrftoken`` cookie (via ``@ensure_csrf_cookie``) so
    the SPA can read it with ``getCsrfToken()`` and include it in POST
    requests to allauth endpoints (login, signup, logout).
    """

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            linked = list(
                request.user.linked_chess_accounts.values(
                    "platform", "platform_username", "is_primary", "rating"
                )
            )
            return JsonResponse({
                "authenticated": True,
                "user": {
                    "id": request.user.id,
                    "username": request.user.username,
                    "email": request.user.email,
                    "linked_accounts": linked,
                },
            })
        return JsonResponse({"authenticated": False})


# ── Profile CRUD ────────────────────────────────────────────────────


@method_decorator(
    ratelimit(key="ip", rate="60/m", method=["GET"], block=True), name="get"
)
class UsernameCheckView(View):
    """Lightweight GET endpoint to check username availability.

    Returns { "available": true/false } without requiring authentication.
    Rate-limited to 60 requests per minute per IP to prevent enumeration.
    """

    def get(self, request, username, *args, **kwargs):
        from accounts.models import User

        available = not User.objects.filter(username__iexact=username).exists()
        return JsonResponse({"available": available})


# ── Linked Chess Accounts CRUD ─────────────────────────────────────


class LinkedAccountsView(View):
    """GET: list linked chess accounts.
    POST: link a new chess account."""

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)

        accounts = list(
            request.user.linked_chess_accounts.values(
                "id", "platform", "platform_username", "is_primary", "rating", "linked_at"
            )
        )
        return JsonResponse({"linked_accounts": accounts})

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)

        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return JsonResponse({"error": "Invalid JSON body."}, status=400)

        platform = data.get("platform", "").strip().lower()
        platform_username = data.get("platform_username", "").strip()
        is_primary = data.get("is_primary", False)

        if platform not in ("chess.com", "lichess"):
            return JsonResponse({"error": "platform must be 'chess.com' or 'lichess'."}, status=400)
        if not platform_username:
            return JsonResponse({"error": "platform_username is required."}, status=400)

        # If marking as primary, unmark any existing primary on the same platform
        if is_primary:
            request.user.linked_chess_accounts.filter(
                platform=platform, is_primary=True
            ).update(is_primary=False)

        account, created = LinkedChessAccount.objects.get_or_create(
            user=request.user,
            platform=platform,
            platform_username=platform_username,
            defaults={"is_primary": is_primary},
        )

        if not created and is_primary and not account.is_primary:
            account.is_primary = True
            account.save(update_fields=["is_primary"])

        return JsonResponse({
            "id": str(account.id),
            "platform": account.platform,
            "platform_username": account.platform_username,
            "is_primary": account.is_primary,
            "created": created,
        }, status=201 if created else 200)


class LinkedAccountDetailView(View):
    """PATCH: update (e.g. toggle is_primary). DELETE: unlink."""

    def patch(self, request, account_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)

        try:
            account = LinkedChessAccount.objects.get(id=account_id, user=request.user)
        except LinkedChessAccount.DoesNotExist:
            return JsonResponse({"error": "Account not found."}, status=404)

        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except Exception:
            return JsonResponse({"error": "Invalid JSON body."}, status=400)

        if "is_primary" in data and data["is_primary"]:
            # Unmark other primary accounts on same platform
            LinkedChessAccount.objects.filter(
                user=request.user, platform=account.platform, is_primary=True
            ).update(is_primary=False)
            account.is_primary = True

        if "rating" in data:
            account.rating = data["rating"]

        account.save(update_fields=["is_primary", "rating"])

        return JsonResponse({
            "id": str(account.id),
            "platform": account.platform,
            "platform_username": account.platform_username,
            "is_primary": account.is_primary,
            "rating": account.rating,
        })

    def delete(self, request, account_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Authentication required."}, status=401)

        try:
            account = LinkedChessAccount.objects.get(id=account_id, user=request.user)
        except LinkedChessAccount.DoesNotExist:
            return JsonResponse({"error": "Account not found."}, status=404)

        account.delete()
        return JsonResponse({"deleted": True})
