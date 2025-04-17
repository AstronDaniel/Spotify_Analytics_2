import re
import requests
from django.shortcuts import render, redirect
from django.contrib import messages
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from django.urls import reverse

class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.pop('timeout', 5)
        super().__init__(*args, **kwargs)
        
    def send(self, request, **kwargs):
        kwargs['timeout'] = self.timeout
        return super().send(request, **kwargs)

class SpotifyServiceUnavailableMiddleware:
    """
    Middleware to catch Spotify API connectivity errors and provide user-friendly responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check if we're in a Spotify auth flow
        if request.path.startswith('/users/spotify-login/') or request.path.startswith('/users/callback/'):
            # Configure session with retries and timeout
            session = requests.Session()
            retry_strategy = Retry(
                total=3,  # Maximum number of retries
                backoff_factor=0.5,  # Wait 0.5s, 1s, 2s between retries
                status_forcelist=[429, 500, 502, 503, 504],  # Retry on these status codes
            )
            adapter = TimeoutHTTPAdapter(max_retries=retry_strategy, timeout=10)  # 10 second timeout
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            # Replace the default requests session
            original_session = requests.Session
            requests.Session = lambda: session
            
            try:
                # Record start time
                start_time = time.time()
                
                # Process the request
                response = self.get_response(request)
                
                # Calculate response time
                response_time = time.time() - start_time
                
                # If response took too long but succeeded, log it
                if response_time > 5:  # 5 seconds threshold
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Spotify API response was slow: {response_time:.2f}s for {request.path}")
                
                return response
                
            except requests.exceptions.ConnectionError:
                # Connection error
                messages.error(request, "Cannot connect to Spotify servers. Please try again later.")
                return render(request, 'users/error.html', {'error_code': '502 (Bad Gateway)'})
            except requests.exceptions.Timeout:
                # Timeout error
                messages.error(request, "Spotify servers are taking too long to respond. Please try again later.")
                return render(request, 'users/error.html', {'error_code': '504 (Gateway Timeout)'})
            except requests.exceptions.HTTPError as e:
                # HTTP error
                match = re.search(r'(\d+)', str(e))
                status_code = match.group(1) if match else 'unknown'
                messages.error(request, f"Spotify servers returned an error (HTTP {status_code}). Please try again later.")
                return render(request, 'users/error.html', {'error_code': f'{status_code}'})
            except Exception as e:
                # Other errors
                messages.error(request, "An unexpected error occurred when connecting to Spotify. Please try again later.")
                return render(request, 'users/error.html', {'error_code': 'unknown'})
            finally:
                # Restore original session
                requests.Session = original_session
        
        # Normal flow
        return self.get_response(request)

class SpotifyAuthMiddleware:
    """Middleware to check for Spotify authentication"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Process request before view is called
        
        # URLs that require Spotify authentication
        spotify_required_urls = [
            '/analytics/dashboard/',
            '/analytics/personal-insights/',
            '/visualization/genre-distribution/',
            '/visualization/audio-features/',
            '/visualization/time-comparison/',
            '/visualization/export-data/',
        ]
        
        # Only enforce for Spotify-required URLs
        if request.path in spotify_required_urls:
            # Check if the user has a Spotify token
            if not request.session.get('spotify_token_info'):
                messages.info(request, "Please connect your Spotify account to access this feature.")
                return redirect('spotify_login')
        
        # Continue processing the request
        response = self.get_response(request)
        return response 