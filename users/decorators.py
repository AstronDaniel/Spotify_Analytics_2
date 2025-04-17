from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages

def spotify_login_required(view_func):
    """
    Decorator to check if the user is authenticated with Spotify.
    If not, redirects to Spotify login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if the user has a Spotify token
        if not request.session.get('spotify_token_info'):
            messages.info(request, "Please connect your Spotify account to access this feature.")
            return redirect('spotify_login')
        return view_func(request, *args, **kwargs)
    return wrapper 