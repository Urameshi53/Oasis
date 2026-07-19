import re

from django.conf import settings
from django.contrib.auth.views import redirect_to_login


class LoginRequiredMiddleware:
    """
    Gate the whole site behind authentication.

    Anonymous visitors are redirected to the login page (which leads with
    "Continue with Google") the moment they open the site, so new users must
    log in or register before browsing. Paths in ``settings.LOGIN_EXEMPT_URLS``
    (the auth flows themselves, admin, the payment callback, the API, static /
    media) stay open so there's no redirect loop or lock-out.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt = [re.compile(p) for p in getattr(settings, "LOGIN_EXEMPT_URLS", [])]
        self.login_url = getattr(settings, "LOGIN_URL", "/accounts/login/")

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            path = request.path_info.lstrip("/")
            if not any(pattern.match(path) for pattern in self.exempt):
                return redirect_to_login(request.get_full_path(), self.login_url)
        return self.get_response(request)
