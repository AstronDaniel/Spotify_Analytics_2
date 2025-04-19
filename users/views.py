from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
import spotipy
import requests
import time
from .spotify_utils import CustomSpotifyOAuth
from django.http import JsonResponse


def login(request):
    """View for the login page"""
    return render(request, 'users/login.html')


def spotify_login(request):
    """Handle Spotify OAuth login"""
    try:
        # Create the SpotifyOAuth object with our custom class
        sp_oauth = CustomSpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope="user-read-recently-played user-top-read user-read-playback-state user-read-currently-playing playlist-read-private user-library-read user-read-private"
        )
        
        # Get the authorization URL
        auth_url = sp_oauth.get_authorize_url()
        
        # Store the state in the session
        request.session['spotify_auth_state'] = sp_oauth.state
        
        # Record the time of the auth request to detect timeouts
        request.session['spotify_auth_start_time'] = time.time()
        
        # Redirect the user to Spotify's authorization page
        return redirect(auth_url)
    except requests.exceptions.HTTPError as e:
        # Check if this is a rate limit error (429)
        if '429' in str(e):
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Spotify rate limit exceeded: {str(e)}")
            messages.error(request, "We've reached Spotify's rate limit. Please try again in a few minutes.")
            return render(request, 'users/error.html', {'error_code': '429 (Too Many Requests)', 'is_rate_limit': True})
        
        # Handle other HTTP errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Spotify HTTP error: {str(e)}")
        messages.error(request, "Error connecting to Spotify. Please try again later.")
        return redirect('home')
    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Spotify authentication error: {str(e)}")
        
        # Show user-friendly message
        messages.error(request, "Spotify authentication service is currently unavailable. Please try again later.")
        return redirect('home')


def callback(request):
    """Handle Spotify OAuth callback"""
    try:
        # Check if the request has taken too long
        start_time = request.session.get('spotify_auth_start_time', 0)
        if start_time > 0:
            elapsed = time.time() - start_time
            if elapsed > 30:  # More than 30 seconds
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Spotify callback took too long: {elapsed:.2f}s")
                messages.warning(request, "Connection to Spotify was slow. Performance may be affected.")
        
        # Get the code from the request
        code = request.GET.get('code')
        
        # Get the state from the request and session
        state = request.GET.get('state')
        stored_state = request.session.get('spotify_auth_state')
        
        # Verify the state
        if state is None or state != stored_state:
            messages.error(request, "State verification failed. Please try again.")
            return redirect('login')
        
        # Create the SpotifyOAuth object with our custom class
        sp_oauth = CustomSpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope="user-read-recently-played user-top-read user-read-playback-state user-read-currently-playing playlist-read-private user-library-read user-read-private"
        )
        
        # Get the access token
        token_info = sp_oauth.get_access_token(code)
        
        # Store the token in the session
        request.session['spotify_token_info'] = token_info
        
        # Create a Spotify client with token
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Creating Spotify client with token: {token_info.get('access_token', '')[:5]}...")
        
        # Use the spotify_client_fix helper to create the client
        from .spotify_client_fix import create_spotify_client
        sp = create_spotify_client(token_info['access_token'])
        logger.debug("Successfully created Spotify client using fix")
        
        # Get the user's profile
        user_profile = sp.current_user()
        
        # Store the user's profile in the session
        request.session['spotify_user_profile'] = user_profile
        
        # Clear the auth timing data
        request.session.pop('spotify_auth_start_time', None)
        
        # Redirect to the dashboard
        messages.success(request, f"Welcome, {user_profile['display_name']}! You are now connected to Spotify.")
        return redirect('dashboard')
            
    except requests.exceptions.HTTPError as e:
        # Check if this is a rate limit error (429)
        if '429' in str(e):
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Spotify rate limit exceeded: {str(e)}")
            messages.error(request, "We've reached Spotify's rate limit. Please try again in a few minutes.")
            return render(request, 'users/error.html', {'error_code': '429 (Too Many Requests)', 'is_rate_limit': True})
        
        # Handle other HTTP errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Spotify HTTP error: {str(e)}")
        messages.error(request, "Error connecting to Spotify. Please try again later.")
        return redirect('login')    
    except Exception as e:
        # Log the error with full traceback
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Spotify callback error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full error details: {traceback.format_exc()}")
        
        # Print to console for immediate debugging
        print(f"\n\n====== SPOTIFY ERROR ======")
        print(f"Error message: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        print(f"Traceback: {traceback.format_exc()}")
        if 'token_info' in locals():
            print(f"Token info keys: {list(token_info.keys()) if token_info else 'No token info'}")
            print(f"Token type: {token_info.get('token_type', 'N/A') if token_info else 'N/A'}")
        print(f"====== END SPOTIFY ERROR ======\n\n")
        
        # Show user-friendly message
        messages.error(request, f"Error connecting to Spotify: {type(e).__name__}. The service might be temporarily unavailable. Please try again later.")
        return redirect('login')


@login_required
def profile(request):
    """View for the user profile page"""
    # Get the token info from the session
    token_info = request.session.get('spotify_token_info')
    
    # If there's no token info, redirect to login
    if not token_info:
        messages.error(request, "You are not connected to Spotify. Please connect your account.")
        return redirect('spotify_login')
    
    # Create the SpotifyOAuth object with our custom class
    sp_oauth = CustomSpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope="user-read-recently-played user-top-read user-read-playback-state user-read-currently-playing playlist-read-private user-library-read user-read-private"
    )
    
    # Refresh the token if needed
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        request.session['spotify_token_info'] = token_info
    
    # Use our custom Spotify client
    from .spotify_client_fix import create_spotify_client
    sp = create_spotify_client(token_info['access_token'])
    
    # Get the user's profile
    user_profile = sp.current_user()
    
    # Get the user's top artists
    top_artists = sp.current_user_top_artists(limit=5, time_range='medium_term')
    
    # Get the user's top tracks
    top_tracks = sp.current_user_top_tracks(limit=5, time_range='medium_term')
    
    # Get the user's playlists
    playlists = sp.current_user_playlists(limit=5)
    
    # Create the context
    context = {
        'user_profile': user_profile,
        'top_artists': top_artists,
        'top_tracks': top_tracks,
        'playlists': playlists,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def settings_view(request):
    """View for the user settings page"""
    return render(request, 'users/settings.html')


def logout(request):
    """Handle user logout"""
    # Clear the session
    request.session.pop('spotify_token_info', None)
    request.session.pop('spotify_user_profile', None)
    request.session.pop('spotify_auth_state', None)
    
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')


@login_required
def delete_data(request):
    """Handle user data deletion"""
    if request.method == 'POST':
        # Get the token info from the session
        token_info = request.session.get('spotify_token_info')
        
        # Here you would implement the actual data deletion logic
        # For example, delete user data from your database
        # This is a placeholder for where you'd add that code
        
        # Clear the session data
        request.session.pop('spotify_token_info', None)
        request.session.pop('spotify_user_profile', None)
        request.session.pop('spotify_auth_state', None)
        
        messages.success(request, "Your data has been successfully deleted.")
        return redirect('home')
    
    # If not a POST request, redirect to settings
    return redirect('settings')


def debug_spotify(request):
    """
    Debug view to examine the Spotipy library structure.
    This is a temporary view to help diagnose the issue.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    import inspect
    import spotipy
    import sys
    
    debug_info = {}
    
    # Examine the SpotifyOAuth class
    debug_info['spotipy_version'] = spotipy.__version__
    debug_info['python_version'] = sys.version
    
    # Check the SpotifyAuthBase class
    debug_info['SpotifyAuthBase_attributes'] = dir(spotipy.oauth2.SpotifyAuthBase)
    debug_info['SpotifyAuthBase_has_del'] = hasattr(spotipy.oauth2.SpotifyAuthBase, '__del__')
    
    # Check SpotifyOAuth
    debug_info['SpotifyOAuth_attributes'] = dir(spotipy.oauth2.SpotifyOAuth)
    debug_info['SpotifyOAuth_has_del'] = hasattr(spotipy.oauth2.SpotifyOAuth, '__del__')
    
    # Log all findings
    for key, value in debug_info.items():
        logger.debug("%s: %s", key, value)
    
    # Create a SpotifyOAuth instance and examine it
    try:
        sp_oauth = spotipy.oauth2.SpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope="user-read-private"
        )
        debug_info['SpotifyOAuth_instance_attributes'] = dir(sp_oauth)
        debug_info['SpotifyOAuth_instance_has_session'] = hasattr(sp_oauth, '_session')
        if hasattr(sp_oauth, '_session'):
            debug_info['SpotifyOAuth_session_type'] = type(sp_oauth._session).__name__
    except Exception as e:
        debug_info['SpotifyOAuth_instance_error'] = str(e)
    
    # Create a CustomSpotifyOAuth instance and examine it
    try:
        from .spotify_utils import CustomSpotifyOAuth
        custom_oauth = CustomSpotifyOAuth(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET,
            redirect_uri=settings.SPOTIFY_REDIRECT_URI,
            scope="user-read-private"
        )
        debug_info['CustomSpotifyOAuth_instance_attributes'] = dir(custom_oauth)
        debug_info['CustomSpotifyOAuth_instance_has_session'] = hasattr(custom_oauth, '_session')
        if hasattr(custom_oauth, '_session'):
            debug_info['CustomSpotifyOAuth_session_type'] = type(custom_oauth._session).__name__
    except Exception as e:
        debug_info['CustomSpotifyOAuth_instance_error'] = str(e)
    
    # Return JSON response with all debug info
    return JsonResponse({'debug_info': debug_info})
