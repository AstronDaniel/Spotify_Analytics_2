"""
Spotify API client wrapper that avoids the problematic isinstance() error in spotipy.
This module provides a direct implementation that bypasses the broken code path.
"""
import logging
import json
import requests
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class SpotifyClient:
    """
    Custom Spotify API client that doesn't rely on spotipy's problematic code path.
    This is a minimal implementation that covers the basic functionality needed.
    """
    
    API_BASE_URL = "https://api.spotify.com/v1"
    
    def __init__(self, auth=None):
        """Initialize the client with an access token"""
        self.auth = auth
        self.session = requests.Session()
        logger.debug("Created SpotifyClient with auth token starting with: %s", 
                    auth[:5] + "..." if auth else "None")
    
    def __del__(self):
        """Clean up the session when the client is destroyed"""
        try:
            if hasattr(self, 'session') and self.session:
                self.session.close()
                logger.debug("Closed SpotifyClient session")
        except Exception as e:
            logger.warning("Error closing SpotifyClient session: %s", str(e))
    
    def _api_request(self, method, url, **kwargs):
        """Make a request to the Spotify API"""
        # Add the authorization header
        headers = kwargs.pop('headers', {})
        headers['Authorization'] = f"Bearer {self.auth}"
        
        # Make the request
        full_url = f"{self.API_BASE_URL}/{url.lstrip('/')}" if not url.startswith('http') else url
        logger.debug("%s request to %s", method.upper(), full_url)
        
        response = self.session.request(
            method=method,
            url=full_url,
            headers=headers,
            **kwargs
        )
        
        # Check for errors
        if response.status_code >= 400:
            logger.error("API error: %s - %s", response.status_code, response.text)
            response.raise_for_status()
        
        # Return the parsed JSON response
        if response.text and response.text != 'null':
            return response.json()
        else:
            return None
    
    def get(self, url, **kwargs):
        """Make a GET request to the Spotify API"""
        return self._api_request('GET', url, **kwargs)
    
    def post(self, url, **kwargs):
        """Make a POST request to the Spotify API"""
        return self._api_request('POST', url, **kwargs)
    
    def put(self, url, **kwargs):
        """Make a PUT request to the Spotify API"""
        return self._api_request('PUT', url, **kwargs)
    
    def delete(self, url, **kwargs):
        """Make a DELETE request to the Spotify API"""
        return self._api_request('DELETE', url, **kwargs)
    
    # Add specific API methods below
    
    def current_user(self):
        """Get detailed profile information about the current user"""
        return self.get('me')
    
    def current_user_top_artists(self, limit=20, offset=0, time_range='medium_term'):
        """Get the current user's top artists"""
        params = {
            'limit': limit,
            'offset': offset,
            'time_range': time_range
        }
        url = f"me/top/artists?{urlencode(params)}"
        return self.get(url)
    
    def current_user_top_tracks(self, limit=20, offset=0, time_range='medium_term'):
        """Get the current user's top tracks"""
        params = {
            'limit': limit,
            'offset': offset,
            'time_range': time_range
        }
        url = f"me/top/tracks?{urlencode(params)}"
        return self.get(url)
    
    def current_user_playlists(self, limit=20, offset=0):
        """Get a list of the playlists owned or followed by the current user"""
        params = {
            'limit': limit,
            'offset': offset
        }
        url = f"me/playlists?{urlencode(params)}"
        return self.get(url)
    
    def current_user_recently_played(self, limit=20, after=None, before=None):
        """Get the current user's recently played tracks"""
        params = {'limit': limit}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        
        url = f"me/player/recently-played?{urlencode(params)}"
        return self.get(url)
        
    def get_recommendations(self, seed_tracks=None, seed_artists=None, seed_genres=None, limit=20, **kwargs):
        """Get recommendations based on seeds"""
        params = {'limit': limit}
        
        if seed_tracks:
            if isinstance(seed_tracks, list):
                seed_tracks = ','.join(seed_tracks)
            params['seed_tracks'] = seed_tracks
            
        if seed_artists:
            if isinstance(seed_artists, list):
                seed_artists = ','.join(seed_artists)
            params['seed_artists'] = seed_artists
            
        if seed_genres:
            if isinstance(seed_genres, list):
                seed_genres = ','.join(seed_genres)
            params['seed_genres'] = seed_genres
            
        # Add any additional parameters
        for key, value in kwargs.items():
            params[key] = value
            
        url = f"recommendations?{urlencode(params)}"
        return self.get(url)
    
    def get_artist(self, artist_id):
        """Get an artist by ID"""
        return self.get(f"artists/{artist_id}")
    
    def get_artists(self, artist_ids):
        """Get several artists by ID"""
        if isinstance(artist_ids, list):
            artist_ids = ','.join(artist_ids)
        return self.get(f"artists?ids={artist_ids}")
    
    def get_artist_albums(self, artist_id, album_type=None, limit=20, offset=0):
        """Get an artist's albums"""
        params = {
            'limit': limit,
            'offset': offset
        }
        if album_type:
            params['album_type'] = album_type
            
        url = f"artists/{artist_id}/albums?{urlencode(params)}"
        return self.get(url)
    
    def get_artist_top_tracks(self, artist_id, country='US'):
        """Get an artist's top tracks"""
        url = f"artists/{artist_id}/top-tracks?country={country}"
        return self.get(url)
    
    def get_artist_related_artists(self, artist_id):
        """Get artists related to an artist"""
        return self.get(f"artists/{artist_id}/related-artists")
    
    def get_track(self, track_id):
        """Get a track by ID"""
        return self.get(f"tracks/{track_id}")
    
    def get_tracks(self, track_ids):
        """Get several tracks by ID"""
        if isinstance(track_ids, list):
            track_ids = ','.join(track_ids)
        return self.get(f"tracks?ids={track_ids}")
    
    def get_audio_features(self, track_id):
        """Get audio features for a track"""
        return self.get(f"audio-features/{track_id}")
    def get_audio_features_for_tracks(self, track_ids):
        """Get audio features for several tracks"""
        if isinstance(track_ids, list):
            track_ids = ','.join(track_ids)
        response = self.get(f"audio-features?ids={track_ids}")
        return {'audio_features': response}
    
    def get_album(self, album_id):
        """Get an album by ID"""
        return self.get(f"albums/{album_id}")
    
    def get_album_tracks(self, album_id, limit=50, offset=0):
        """Get an album's tracks"""
        params = {
            'limit': limit,
            'offset': offset
        }
        url = f"albums/{album_id}/tracks?{urlencode(params)}"
        return self.get(url)

def create_spotify_client(token):
    """
    Create a custom Spotify client using the access token.
    This avoids the problematic code path in the spotipy library.
    
    Args:
        token (str): The Spotify access token
        
    Returns:
        SpotifyClient: A custom Spotify client instance
    """
    logger.debug("Creating custom SpotifyClient instance")
    return SpotifyClient(auth=token)
