import spotipy
from spotipy.oauth2 import SpotifyOAuth as BaseSpotifyOAuth
import requests
import logging
import traceback
import sys
import inspect
import time
import random
import string
import os
import base64

# Update the logger configuration
logger = logging.getLogger('users.spotify_utils')  # Use the fully qualified logger name
# Don't set the level here, let settings.py control it
# logger.setLevel(logging.DEBUG)

# Let's examine the SpotifyOAuth class structure
logger.debug("Base SpotifyOAuth methods: %s", dir(BaseSpotifyOAuth))
logger.debug("Has __del__: %s", hasattr(BaseSpotifyOAuth, "__del__"))

class CustomSpotifyOAuth(BaseSpotifyOAuth):
    """
    Custom implementation of SpotifyOAuth that fixes the _session attribute issue
    and provides additional error handling with detailed diagnostics.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Complete override of __init__ to avoid calling super().__init__()
        which has the problematic isinstance() check.
        """
        logger.debug("CustomSpotifyOAuth.__init__ called with args: %s, kwargs: %s", args, kwargs)
        try:
            # Initialize _session directly
            self._session = requests.Session()
            logger.debug("Created self._session: %s", self._session)
            
            # Initialize all required attributes directly from kwargs
            self.client_id = kwargs.get('client_id')
            self.client_secret = kwargs.get('client_secret')
            self.redirect_uri = kwargs.get('redirect_uri')
            if self.redirect_uri and '\\x3a' in self.redirect_uri:
                # Fix escaped characters in the redirect URI
                self.redirect_uri = self.redirect_uri.replace('\\x3a', ':')
                logger.debug(f"Fixed escaped characters in redirect_uri: {self.redirect_uri}")
            self.cache_path = kwargs.get('cache_path')
            self.scope = kwargs.get('scope', '')
            self.proxies = kwargs.get('proxies', None)
            self.requests_timeout = kwargs.get('requests_timeout', None)
            self.open_browser = kwargs.get('open_browser', True)
            self.cache_handler = kwargs.get('cache_handler', None)
            self.username = kwargs.get('username')
            self.show_dialog = kwargs.get('show_dialog', False)
            
            # Generate a new random state
            self.state = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
            
            # Initialize other attributes
            self.OAUTH_AUTHORIZE_URL = 'https://accounts.spotify.com/authorize'
            self.OAUTH_TOKEN_URL = 'https://accounts.spotify.com/api/token'
            
            logger.debug("Successfully initialized CustomSpotifyOAuth")
        except Exception as e:
            logger.error("Error in CustomSpotifyOAuth.__init__: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise
    
    def __del__(self):
        """
        Complete override of the __del__ method to avoid the isinstance() error.
        Added extensive logging to track the issue.
        """
        logger.debug("CustomSpotifyOAuth.__del__ called")
        try:
            # Log the object state
            logger.debug("In __del__, self attributes: %s", dir(self))
            logger.debug("self._session exists: %s", hasattr(self, '_session'))
            
            # Simple direct check and close
            if hasattr(self, '_session'):
                logger.debug("self._session type: %s", type(self._session))
                if hasattr(self._session, 'close'):
                    logger.debug("Calling self._session.close()")
                    self._session.close()
                else:
                    logger.debug("self._session has no close method")
        except Exception as e:
            # Log but don't propagate any errors
            logger.error("Error in CustomSpotifyOAuth.__del__: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
    
    def get_authorize_url(self, *args, **kwargs):
        """
        Reimplement get_authorize_url to not rely on super()
        Generates the URL for the authorization page.
        """
        logger.debug("CustomSpotifyOAuth.get_authorize_url called with args: %s, kwargs: %s", args, kwargs)
        try:
            # Get state from kwargs or use the existing one
            state = kwargs.get('state', self.state)
            
            # Build the auth URL
            params = {
                'client_id': self.client_id,
                'response_type': 'code',
                'redirect_uri': self.redirect_uri,
                'state': state,
            }
            
            if self.scope:
                params['scope'] = self.scope
                
            if kwargs.get('show_dialog', self.show_dialog):
                params['show_dialog'] = 'true'
                
            # Construct the URL with parameters - make sure to properly encode each parameter
            auth_url = self.OAUTH_AUTHORIZE_URL + '?' + '&'.join(
                [f"{k}={requests.utils.quote(str(v), safe='')}" for k, v in params.items()]
            )
            
            logger.debug("Authorization URL generated successfully: %s", auth_url[:50] + "..." if len(auth_url) > 50 else auth_url)
            return auth_url
        except Exception as e:
            logger.error("Error getting Spotify authorization URL: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise Exception(f"Failed to connect to Spotify: {str(e)}")
    
    def get_access_token(self, code=None, check_cache=True):
        """
        Reimplement get_access_token to not rely on super()
        Gets the access token for the user.
        """
        logger.debug("CustomSpotifyOAuth.get_access_token called with code: %s, check_cache: %s", 
                   "REDACTED" if code else None, check_cache)
        try:
            if code is None and check_cache:
                # Try to get token from cache
                if self.cache_handler:
                    token_info = self.cache_handler.get_cached_token()
                    if token_info and not self.is_token_expired(token_info):
                        logger.debug("Using cached token")
                        return token_info
            
            if code is None:
                logger.debug("No code provided and no cached token found")
                return None
            
            # Exchange the code for an access token
            payload = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self.redirect_uri,
            }
            
            headers = self._make_authorization_headers()
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            response = self._session.post(
                self.OAUTH_TOKEN_URL,
                data=payload,
                headers=headers,
                verify=True,
                proxies=self.proxies,
                timeout=self.requests_timeout
            )
            
            if response.status_code != 200:
                self._handle_oauth_error(response)
            
            token_info = response.json()
            token_info = self._add_custom_values_to_token_info(token_info)
            
            # Cache the token if a cache handler is available
            if self.cache_handler:
                self.cache_handler.save_token_to_cache(token_info)
                
            logger.debug("Access token retrieved successfully")
            return token_info
        except Exception as e:
            logger.error("Error getting Spotify access token: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise Exception(f"Failed to retrieve Spotify access token: {str(e)}")
            
    def is_token_expired(self, token_info):
        """
        Reimplement is_token_expired to not rely on super()
        Checks if the token is expired.
        """
        logger.debug("CustomSpotifyOAuth.is_token_expired called with token_info: %s", 
                   {k: "REDACTED" if k in ["access_token", "refresh_token"] else v 
                    for k, v in token_info.items()} if token_info else None)
        try:
            now = int(time.time())
            return token_info['expires_at'] - now < 60
        except Exception as e:
            logger.error("Error checking if token is expired: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            # Default to expired if we can't check
            logger.debug("Defaulting to token expired=True due to error")
            return True
            
    def refresh_access_token(self, refresh_token):
        """
        Reimplement refresh_access_token to not rely on super()
        Refreshes the access token with the refresh token.
        """
        logger.debug("CustomSpotifyOAuth.refresh_access_token called with refresh_token: REDACTED")
        try:
            payload = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
            }
            
            headers = self._make_authorization_headers()
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            
            response = self._session.post(
                self.OAUTH_TOKEN_URL,
                data=payload,
                headers=headers,
                verify=True,
                proxies=self.proxies,
                timeout=self.requests_timeout
            )
            
            if response.status_code != 200:
                self._handle_oauth_error(response)
            
            token_info = response.json()
            if 'refresh_token' not in token_info:
                token_info['refresh_token'] = refresh_token
            
            token_info = self._add_custom_values_to_token_info(token_info)
            
            # Cache the token if a cache handler is available
            if self.cache_handler:
                self.cache_handler.save_token_to_cache(token_info)
                
            logger.debug("Token refreshed successfully")
            return token_info
        except Exception as e:
            logger.error("Error refreshing access token: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise Exception(f"Failed to refresh Spotify access token: {str(e)}")
    
    def get_auth_response(self, open_browser=None):
        """
        Get the authorization code by various means.
        """
        logger.debug("CustomSpotifyOAuth.get_auth_response called with open_browser: %s", open_browser)
        
        if open_browser is None:
            open_browser = self.open_browser
            
        try:
            if open_browser:
                # Use the local server to get the authorization code
                return self._get_auth_response_local_server()
            else:
                # Use the interactive shell to get the authorization code
                return self._get_auth_response_interactive()
        except Exception as e:
            logger.error("Error getting authentication response: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise
    
    def _get_auth_response_local_server(self):
        """
        Setup a local server to receive the authorization code via redirect.
        """
        logger.debug("CustomSpotifyOAuth._get_auth_response_local_server called")
        try:
            # Get the authorization URL
            url = self.get_authorize_url()
            
            # Import modules needed for this method
            import webbrowser
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import socket
            from urllib.parse import urlparse, parse_qs
            
            # Define a request handler to capture the code from the redirect
            class RequestHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    # Parse the query parameters from the URL
                    query = urlparse(self.path).query
                    params = parse_qs(query)
                    
                    # Send a response to the browser
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html')
                    self.end_headers()
                    
                    # HTML response for the user
                    self.wfile.write(b'<html><body><h1>Authentication Successful!</h1>')
                    self.wfile.write(b'<p>You can now close this window and return to the application.</p>')
                    self.wfile.write(b'</body></html>')
                    
                    # Store the response parameters
                    self.server.auth_response = self.path
                
                # Silence the log messages
                def log_message(self, format, *args):
                    pass
            
            # Create a server on localhost with a random port
            server = HTTPServer(('localhost', 0), RequestHandler)
            server.auth_response = None
            
            # Get the port that was assigned
            port = server.server_port
            
            # Open the browser with the authorization URL
            webbrowser.open(url)
            
            # Timeout after 5 minutes
            server.timeout = 300
            
            # Start the server and wait for the response
            server.handle_request()
            
            # Check if we got a response
            if server.auth_response is None:
                raise Exception("No authorization response received")
            
            # Return the full response URL
            return server.auth_response
        except Exception as e:
            logger.error("Error in local server authentication: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise
    
    def _get_auth_response_interactive(self):
        """
        Get the authorization response by having the user manually copy and paste.
        """
        logger.debug("CustomSpotifyOAuth._get_auth_response_interactive called")
        try:
            # Get the authorization URL
            url = self.get_authorize_url()
            
            # Print instructions for the user
            print(f"\nPlease navigate to this URL in your browser: {url}\n")
            print("After authenticating, you will be redirected to a URL. Please copy and paste that URL here:")
            
            # Get the response URL from the user
            response = self._get_user_input("Enter the URL you were redirected to: ")
            
            return response
        except Exception as e:
            logger.error("Error in interactive authentication: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise
    
    def _get_user_input(self, prompt):
        """
        Get user input from the console.
        """
        try:
            return input(prompt)
        except KeyboardInterrupt:
            raise Exception("User cancelled the authentication process")
    
    def parse_response_code(self, url):
        """
        Parse the response code from the URL.
        """
        logger.debug("CustomSpotifyOAuth.parse_response_code called with url: %s", url[:50] + "..." if len(url) > 50 else url)
        try:
            # Import modules needed for this method
            from urllib.parse import urlparse, parse_qs
            
            # Parse the URL
            parsed = urlparse(url)
            
            # Handle cases where the response is a query parameter or path segment
            if '?' in url:
                # Normal case where code is a parameter like ?code=...
                qs = parse_qs(parsed.query)
                if 'code' in qs:
                    return qs['code'][0]
            else:
                # Handle case where redirect URI has no parameters and code is a path segment
                code = parsed.path.split('/')[-1]
                if code:
                    return code
            
            # If we got here, we didn't find a code
            raise Exception("No code found in URL")
        except Exception as e:
            logger.error("Error parsing response code: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise
            
    def parse_auth_response_url(self, url):
        """
        Parse the full authorization response URL.
        """
        logger.debug("CustomSpotifyOAuth.parse_auth_response_url called with url: %s", url[:50] + "..." if len(url) > 50 else url)
        try:
            # Import modules needed for this method
            from urllib.parse import urlparse, parse_qs
            
            # Parse the URL
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            
            # Check for state
            if 'state' in qs:
                state = qs['state'][0]
                # Validate the state matches what we sent
                if state != self.state:
                    raise Exception(f"State mismatch: expected {self.state}, got {state}")
            
            # Get the code
            code = self.parse_response_code(url)
            
            return code
        except Exception as e:
            logger.error("Error parsing auth response URL: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise
            
    def get_authorization_code(self, *args, **kwargs):
        """
        Get the authorization code.
        """
        logger.debug("CustomSpotifyOAuth.get_authorization_code called")
        try:
            # Get the response from the auth flow
            response = self.get_auth_response()
            
            # Parse the response to get the code
            code = self.parse_auth_response_url(response)
            
            return code
        except Exception as e:
            logger.error("Error getting authorization code: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            raise
            
    def get_cached_token(self):
        """
        Get the cached token if available.
        """
        logger.debug("CustomSpotifyOAuth.get_cached_token called")
        try:
            if self.cache_handler:
                return self.cache_handler.get_cached_token()
            return None
        except Exception as e:
            logger.error("Error getting cached token: %s", str(e))
            logger.error("Traceback: %s", traceback.format_exc())
            return None

    def _normalize_scope(self, scope):
        """
        Normalize the scope to a string.
        """
        if scope:
            if isinstance(scope, list):
                return ' '.join(sorted(scope))
            elif isinstance(scope, str):
                return scope
        return ''

    def _is_scope_subset(self, current_scope, desired_scope):
        """
        Check if the desired scope is a subset of the current scope.
        """
        if not desired_scope:
            return True

        current_scope = self._normalize_scope(current_scope)
        desired_scope = self._normalize_scope(desired_scope)

        current_scopes = set(current_scope.split(' ') if current_scope else [])
        desired_scopes = set(desired_scope.split(' ') if desired_scope else [])

        return desired_scopes.issubset(current_scopes)

    def _make_authorization_headers(self):
        """
        Build the Authorization header for API calls.
        """
        auth_header = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode("ascii")
        )
        return {"Authorization": f"Basic {auth_header.decode('ascii')}"}

    def _handle_oauth_error(self, response):
        """
        Handle OAuth errors from the Spotify API.
        """
        if response.status_code >= 400:
            error = response.json().get("error", "")
            error_desc = response.json().get("error_description", "")
            raise Exception(f"OAuth error: {error} - {error_desc}")
        
    def _add_custom_values_to_token_info(self, token_info):
        """
        Add custom values to the token info.
        """
        if "expires_in" in token_info:
            token_info["expires_at"] = int(time.time()) + token_info["expires_in"]
        return token_info 