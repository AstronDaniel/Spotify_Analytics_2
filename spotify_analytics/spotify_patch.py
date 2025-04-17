"""
Direct patch for the Spotipy library to fix the __del__ method issue.
This is a workaround for the 'isinstance() arg 2 must be a type' error.
"""

import logging
import inspect
import importlib
import types

logger = logging.getLogger(__name__)

def apply_patches():
    """Apply patches to the Spotipy library to fix known issues."""
    try:
        # Import the spotipy module
        import spotipy.oauth2
        
        # Create a completely new __del__ method that doesn't use isinstance
        def safe_del(self):
            """Safe replacement for __del__ that doesn't use isinstance."""
            try:
                if hasattr(self, '_session'):
                    if hasattr(self._session, 'close'):
                        self._session.close()
            except:
                pass
        
        # Get the SpotifyAuthBase class
        auth_base = spotipy.oauth2.SpotifyAuthBase
        
        # Check if __del__ is in the class dict directly
        has_del = '__del__' in auth_base.__dict__
        logger.debug("SpotifyAuthBase has __del__ in its __dict__: %s", has_del)
        
        # Get the mro (method resolution order) to see where __del__ might be coming from
        mro = inspect.getmro(auth_base)
        logger.debug("SpotifyAuthBase MRO: %s", mro)
        
        # Try a few different approaches to patch the method
        
        # Approach 1: Direct assignment
        try:
            auth_base.__del__ = safe_del
            logger.debug("Successfully replaced __del__ using direct assignment")
        except Exception as e:
            logger.debug("Direct assignment failed: %s", str(e))
        
        # Approach 2: Using setattr
        try:
            setattr(auth_base, '__del__', safe_del)
            logger.debug("Successfully replaced __del__ using setattr")
        except Exception as e:
            logger.debug("setattr approach failed: %s", str(e))
        
        # Approach 3: Monkeypatch by changing the class dictionary
        try:
            if has_del:
                # Modify the class dictionary directly
                auth_base.__dict__['__del__'] = safe_del
                logger.debug("Successfully modified class dictionary")
        except Exception as e:
            logger.debug("Class dictionary modification failed: %s", str(e))
        
        # Approach 4: Complete class replacement
        try:
            # Create a new SpotifyAuthBase class that doesn't have the problematic __del__
            class SafeSpotifyAuthBase(object):
                def __init__(self, *args, **kwargs):
                    self._session = None
                    
                def __del__(self):
                    # Our safe version
                    try:
                        if hasattr(self, '_session'):
                            if hasattr(self._session, 'close'):
                                self._session.close()
                    except:
                        pass
            
            # Add all the attributes and methods from the original class
            for name, attr in inspect.getmembers(auth_base):
                if name not in ['__init__', '__del__', '__class__', '__dict__', '__weakref__']:
                    setattr(SafeSpotifyAuthBase, name, attr)
            
            # Replace the original class in the module
            spotipy.oauth2.SpotifyAuthBase = SafeSpotifyAuthBase
            logger.debug("Successfully replaced SpotifyAuthBase with SafeSpotifyAuthBase")
        except Exception as e:
            logger.debug("Complete class replacement failed: %s", str(e))
        
        # Verify the patch worked
        try:
            # Create a test instance
            test_auth = spotipy.oauth2.SpotifyOAuth(
                client_id="test",
                client_secret="test",
                redirect_uri="test"
            )
            
            # Check if the session attribute is there
            logger.debug("Test instance has _session attribute: %s", hasattr(test_auth, '_session'))
            
            # Try to call the __del__ method directly
            if hasattr(test_auth, '__del__'):
                test_auth.__del__()
                logger.debug("Called __del__ method successfully")
            
            logger.debug("Patch verification complete")
        except Exception as e:
            logger.debug("Patch verification failed: %s", str(e))
        
        logger.info("Spotipy library patching complete")
        return True
    
    except Exception as e:
        logger.error("Failed to patch Spotipy library: %s", str(e))
        import traceback
        logger.error("Traceback: %s", traceback.format_exc())
        return False 