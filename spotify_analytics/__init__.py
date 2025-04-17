"""
Spotify Analytics project initialization.
This module contains global fixes and configurations.
"""

import logging
import sys
import traceback
import os
from logging.config import dictConfig
from django.conf import settings

# Force configure logging early
try:
    # Get directory where this file is located
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(BASE_DIR, 'spotify_debug.log')
    
    # Check if log file is writable
    try:
        # Try to write to the log file directly to verify we can
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.write("Testing log file writability\n")
                print(f"Created log file: {log_file}")
        else:
            # Check if the file is writable
            if os.access(log_file, os.W_OK):
                with open(log_file, 'a') as f:
                    f.write("Testing log file writability\n")
                    print(f"Log file is writable: {log_file}")
            else:
                print(f"WARNING: Log file exists but is not writable: {log_file}")
    except Exception as e:
        print(f"WARNING: Cannot write to log file: {log_file} - Error: {str(e)}")
    
    # Simple basic logging config to ensure logs are captured
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': log_file,
                'formatter': 'verbose',
                'mode': 'a',  # Append to file
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    }
    
    # Apply basic config before Django's settings are loaded
    dictConfig(LOGGING)
    
    # Test log entry
    logger = logging.getLogger(__name__)
    logger.debug("Logging initialized in spotify_analytics/__init__.py")
except Exception as e:
    # If logging setup fails, at least print to console
    print(f"Error setting up logging: {str(e)}")
    traceback.print_exc()

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Apply monkey patch to fix Spotipy library issues
try:
    import spotipy.oauth2
    import inspect
    
    # Print diagnostic information about the SpotifyAuthBase class
    logger.debug("SpotifyAuthBase methods: %s", dir(spotipy.oauth2.SpotifyAuthBase))
    logger.debug("SpotifyAuthBase.__del__ exists: %s", hasattr(spotipy.oauth2.SpotifyAuthBase, '__del__'))
    
    if hasattr(spotipy.oauth2.SpotifyAuthBase, '__del__'):
        # Get source code of the problematic method if possible
        try:
            del_source = inspect.getsource(spotipy.oauth2.SpotifyAuthBase.__del__)
            logger.debug("SpotifyAuthBase.__del__ source code: \n%s", del_source)
        except Exception as e:
            logger.debug("Could not get source code for __del__: %s", str(e))
    
    # More aggressive approach: completely remove the __del__ method
    try:
        # First attempt: Try to completely remove the problematic method
        delattr(spotipy.oauth2.SpotifyAuthBase, '__del__')
        logger.debug("Successfully removed SpotifyAuthBase.__del__ method")
    except (AttributeError, TypeError) as e:
        logger.debug("Could not remove __del__ method: %s", str(e))
        
        # Second attempt: Override with a safe version
        def safe_del(self):
            """Safe replacement for the problematic __del__ method"""
            try:
                # Only close the session if it exists and has a close method
                if hasattr(self, '_session'):
                    if hasattr(self._session, 'close'):
                        self._session.close()
            except Exception as e:
                # Log but don't propagate any errors
                logger.debug("Error in safe_del: %s", str(e))
        
        # Replace the problematic __del__ method
        try:
            spotipy.oauth2.SpotifyAuthBase.__del__ = safe_del
            logger.debug("Successfully replaced SpotifyAuthBase.__del__ with safe version")
        except Exception as e:
            logger.debug("Could not replace __del__ method: %s", str(e))
    
    # Try to inspect the SpotifyOAuth class directly
    logger.debug("SpotifyOAuth methods: %s", dir(spotipy.oauth2.SpotifyOAuth))
    logger.debug("SpotifyOAuth.__del__ exists: %s", hasattr(spotipy.oauth2.SpotifyOAuth, '__del__'))
    
    # Attempt to directly fix SpotifyOAuth as well
    try:
        if hasattr(spotipy.oauth2.SpotifyOAuth, '__del__'):
            spotipy.oauth2.SpotifyOAuth.__del__ = safe_del
            logger.debug("Successfully replaced SpotifyOAuth.__del__ with safe version")
    except Exception as e:
        logger.debug("Could not replace SpotifyOAuth.__del__ method: %s", str(e))
    
except Exception as e:
    # Catch-all for any unexpected errors during patching
    logger.error("Error during SpotifyOAuth monkey patching: %s", str(e))
    # Print the full traceback for debugging
    logger.error("Traceback: %s", traceback.format_exc())
