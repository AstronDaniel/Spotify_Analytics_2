from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import spotipy
import json
import csv
import io
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use Agg backend to avoid GUI issues
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from io import BytesIO
from users.spotify_utils import CustomSpotifyOAuth
from users.decorators import spotify_login_required
from users.spotify_client_fix import create_spotify_client
import logging


@spotify_login_required
def genre_distribution(request):
    """View for genre distribution visualization"""
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
    
    # Use the custom Spotify client
    sp = create_spotify_client(token_info['access_token'])
    
    # Get the user's top artists
    top_artists = sp.current_user_top_artists(limit=50, time_range='medium_term')
    
    # Get the user's top tracks to associate with genres
    top_tracks = sp.current_user_top_tracks(limit=50, time_range='medium_term')
    
    # Extract genres from top artists
    genres = {}
    artist_by_genre = {}  # To track which artists belong to each genre
    
    for artist in top_artists['items']:
        for genre in artist['genres']:
            if genre in genres:
                genres[genre] += 1
                artist_by_genre[genre].append(artist)
            else:
                genres[genre] = 1
                artist_by_genre[genre] = [artist]
    
    # Sort genres by count (descending)
    sorted_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)
    
    # Get the top 10 genres
    top_genres = sorted_genres[:10]
    
    # Create song list by genre
    songs_by_genre = {}
    
    # Associate tracks with genres through their artists
    for track in top_tracks['items']:
        track_artist_id = track['artists'][0]['id']
        
        # Find which genres this track's artist belongs to
        track_genres = []
        for genre, artists in artist_by_genre.items():
            if any(artist['id'] == track_artist_id for artist in artists):
                track_genres.append(genre)
        
        # Add track to all matching genres
        for genre in track_genres:
            if genre in songs_by_genre:
                # Don't add duplicates
                if not any(t['id'] == track['id'] for t in songs_by_genre[genre]):
                    songs_by_genre[genre].append(track)
            else:
                songs_by_genre[genre] = [track]
    
    # Create the context with properly formatted data for Chart.js
    genres_labels = [genre for genre, count in top_genres]
    genres_data = [count for genre, count in top_genres]
    
    # Format data for Chart.js (which expects separate labels and data arrays)
    chart_data = {
        'labels': genres_labels,
        'data': genres_data
    }
    
    # Create genre insights data
    if top_genres:
        primary_genre = top_genres[0][0]
        total_artists = sum(count for genre, count in top_genres)
        primary_genre_percentage = round((top_genres[0][1] / total_artists) * 100)
        
        # Calculate diversity score
        genre_diversity = len(genres)
        if genre_diversity > 20:
            diversity_level = "extremely diverse"
        elif genre_diversity > 15:
            diversity_level = "very diverse"
        elif genre_diversity > 10:
            diversity_level = "diverse"
        elif genre_diversity > 5:
            diversity_level = "somewhat diverse"
        else:
            diversity_level = "focused"
    else:
        primary_genre = ""
        primary_genre_percentage = 0
        diversity_level = "unknown"
    
    context = {
        'top_genres': top_genres,
        'genres_data': json.dumps(chart_data),
        'songs_by_genre': songs_by_genre,
        'artists_by_genre': artist_by_genre,
        'primary_genre': primary_genre,
        'primary_genre_percentage': primary_genre_percentage,
        'diversity_level': diversity_level,
        'genre_count': len(genres),
    }
    
    return render(request, 'visualization/genre_distribution.html', context)


@spotify_login_required
def audio_features(request):
    """View for audio features visualization"""
    # Get the token info from the session
    token_info = request.session.get('spotify_token_info')
    
    # If there's no token info, redirect to login
    if not token_info:
        messages.error(request, "You are not connected to Spotify. Please connect your account.")
        return redirect('spotify_login')
    
    # Create the SpotifyOAuth object
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
    
    # Use the custom Spotify client
    sp = create_spotify_client(token_info['access_token'])
    
    try:
        # Get the user's top tracks just to display relevant track info
        top_tracks = sp.current_user_top_tracks(limit=20, time_range='medium_term')
        
        # NOTE: As of November 2024, Spotify restricted access to the audio-features 
        # endpoint for development apps. Since we cannot access audio features,
        # we'll use realistic placeholder data based on average values.
        
        # Create a logger for informational purposes
        logger = logging.getLogger(__name__)
        logger.info("Using placeholder audio feature data due to Spotify API restrictions")
        
        # Generate realistic placeholder data with a bit of randomness
        import random
        track_count = min(len(top_tracks['items']), 20)
        
        # Send a notice to the user
        messages.info(request, f"Audio features provided are sample data. Spotify has restricted access to the audio features API for new applications.")
        
        # Create realistic average features with some variation
        features_avg = {
            'danceability': round(random.uniform(0.55, 0.65), 2),  # Typically 0.5-0.7
            'energy': round(random.uniform(0.55, 0.75), 2),  # Typically 0.5-0.8
            'valence': round(random.uniform(0.45, 0.65), 2),  # Typically 0.4-0.7
            'tempo': round(random.uniform(115, 125), 0),  # Typically 110-130
            'acousticness': round(random.uniform(0.15, 0.35), 2),  # Typically 0.1-0.4
            'instrumentalness': round(random.uniform(0.05, 0.15), 2),  # Typically 0.05-0.2
            'liveness': round(random.uniform(0.15, 0.25), 2),  # Typically 0.1-0.3
            'speechiness': round(random.uniform(0.05, 0.15), 2),  # Typically 0.03-0.1
        }
        
        # Create the context
        context = {
            'features_avg': features_avg,
            'features_data': json.dumps(features_avg),
            'top_tracks': top_tracks['items'][:5],  # Include some tracks for display
        }
        
        return render(request, 'visualization/audio_features.html', context)
        
    except Exception as e:
        messages.error(request, f"Error retrieving data: {str(e)}")
        # Return default data in case of error
        context = {
            'features_avg': {
                'danceability': 0.6,
                'energy': 0.65,
                'valence': 0.5,
                'tempo': 120,
                'acousticness': 0.25,
                'instrumentalness': 0.1,
                'liveness': 0.2,
                'speechiness': 0.1,
            },
            'features_data': json.dumps({
                'danceability': 0.6,
                'energy': 0.65,
                'valence': 0.5,
                'tempo': 120,
                'acousticness': 0.25,
                'instrumentalness': 0.1,
                'liveness': 0.2,
                'speechiness': 0.1,
            }),
        }
        return render(request, 'visualization/audio_features.html', context)


@spotify_login_required
def time_comparison(request):
    """View for time-based comparison visualization"""
    # Get the token info from the session
    token_info = request.session.get('spotify_token_info')
    
    # If there's no token info, redirect to login
    if not token_info:
        messages.error(request, "You are not connected to Spotify. Please connect your account.")
        return redirect('spotify_login')
    
    # Create the SpotifyOAuth object
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
    
    # Use the custom Spotify client
    sp = create_spotify_client(token_info['access_token'])
    
    try:
        # Get the user's top artists for different time ranges
        top_artists_short = sp.current_user_top_artists(limit=10, time_range='short_term')
        top_artists_medium = sp.current_user_top_artists(limit=10, time_range='medium_term')
        top_artists_long = sp.current_user_top_artists(limit=10, time_range='long_term')
        
        # Get the user's top tracks for different time ranges
        top_tracks_short = sp.current_user_top_tracks(limit=10, time_range='short_term')
        top_tracks_medium = sp.current_user_top_tracks(limit=10, time_range='medium_term')
        top_tracks_long = sp.current_user_top_tracks(limit=10, time_range='long_term')
        
        # Get the user's profile for personalization
        user_profile = sp.current_user()
        
        # Prepare data for visualization
        short_term_data = {artist['name']: i for i, artist in enumerate(top_artists_short['items'], 1)}
        medium_term_data = {artist['name']: i for i, artist in enumerate(top_artists_medium['items'], 1)}
        long_term_data = {artist['name']: i for i, artist in enumerate(top_artists_long['items'], 1)}
        
        # Calculate consistency score for artists - how many artists are shared across time periods
        all_artists = set()
        for artist in top_artists_short['items']:
            all_artists.add(artist['name'])
        for artist in top_artists_medium['items']:
            all_artists.add(artist['name'])
        for artist in top_artists_long['items']:
            all_artists.add(artist['name'])
            
        short_term_artist_set = {artist['name'] for artist in top_artists_short['items']}
        medium_term_artist_set = {artist['name'] for artist in top_artists_medium['items']}
        long_term_artist_set = {artist['name'] for artist in top_artists_long['items']}
        
        shared_short_medium_artists = len(short_term_artist_set.intersection(medium_term_artist_set))
        shared_short_long_artists = len(short_term_artist_set.intersection(long_term_artist_set))
        shared_medium_long_artists = len(medium_term_artist_set.intersection(long_term_artist_set))
        
        # Calculate similarity percentages for artists
        similarity_short_medium = int((shared_short_medium_artists / len(short_term_artist_set | medium_term_artist_set)) * 100) if short_term_artist_set and medium_term_artist_set else 0
        similarity_short_long = int((shared_short_long_artists / len(short_term_artist_set | long_term_artist_set)) * 100) if short_term_artist_set and long_term_artist_set else 0
        similarity_medium_long = int((shared_medium_long_artists / len(medium_term_artist_set | long_term_artist_set)) * 100) if medium_term_artist_set and long_term_artist_set else 0
        
        # Calculate consistency score for tracks
        short_term_track_set = {track['name'] for track in top_tracks_short['items']}
        medium_term_track_set = {track['name'] for track in top_tracks_medium['items']}
        long_term_track_set = {track['name'] for track in top_tracks_long['items']}
        
        shared_short_medium_tracks = len(short_term_track_set.intersection(medium_term_track_set))
        shared_short_long_tracks = len(short_term_track_set.intersection(long_term_track_set))
        shared_medium_long_tracks = len(medium_term_track_set.intersection(long_term_track_set))
        
        # Calculate track similarity percentages
        track_similarity_short_medium = int((shared_short_medium_tracks / len(short_term_track_set | medium_term_track_set)) * 100) if short_term_track_set and medium_term_track_set else 0
        track_similarity_short_long = int((shared_short_long_tracks / len(short_term_track_set | long_term_track_set)) * 100) if short_term_track_set and long_term_track_set else 0
        track_similarity_medium_long = int((shared_medium_long_tracks / len(medium_term_track_set | long_term_track_set)) * 100) if medium_term_track_set and long_term_track_set else 0
        
        # Get the most consistent genres across time periods
        genre_counts = {}
        for artist_list in [top_artists_short['items'], top_artists_medium['items'], top_artists_long['items']]:
            for artist in artist_list:
                for genre in artist.get('genres', []):
                    genre_counts[genre] = genre_counts.get(genre, 0) + 1
        
        consistent_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Prepare chart data for artists
        short_term_labels = json.dumps([artist['name'] for artist in top_artists_short['items'][:5]])
        short_term_values = json.dumps([artist.get('popularity', 0) for artist in top_artists_short['items'][:5]])
        
        medium_term_labels = json.dumps([artist['name'] for artist in top_artists_medium['items'][:5]])
        medium_term_values = json.dumps([artist.get('popularity', 0) for artist in top_artists_medium['items'][:5]])
        
        long_term_labels = json.dumps([artist['name'] for artist in top_artists_long['items'][:5]])
        long_term_values = json.dumps([artist.get('popularity', 0) for artist in top_artists_long['items'][:5]])
        
        # Create the context
        context = {
            # User data
            'user_profile': user_profile,
            
            # Artist data
            'short_term_artists': top_artists_short['items'],
            'medium_term_artists': top_artists_medium['items'],
            'long_term_artists': top_artists_long['items'],
            
            # Track data
            'short_term_tracks': top_tracks_short['items'],
            'medium_term_tracks': top_tracks_medium['items'],
            'long_term_tracks': top_tracks_long['items'],
            
            # Range for looping
            'top_artists_range': range(0, 10),  # 0-9 for indexing
            'top_tracks_range': range(0, 10),  # 0-9 for indexing
            
            # Similarity scores
            'similarity_short_medium': similarity_short_medium,
            'similarity_short_long': similarity_short_long,
            'similarity_medium_long': similarity_medium_long,
            
            # Track similarity scores
            'track_similarity_short_medium': track_similarity_short_medium,
            'track_similarity_short_long': track_similarity_short_long,
            'track_similarity_medium_long': track_similarity_medium_long,
            
            # Chart data
            'short_term_labels': short_term_labels,
            'short_term_values': short_term_values,
            'medium_term_labels': medium_term_labels,
            'medium_term_values': medium_term_values,
            'long_term_labels': long_term_labels,
            'long_term_values': long_term_values,
            
            # Genre data
            'consistent_genres': consistent_genres,
        }
        
        # Add trend analysis if there's enough data
        if top_artists_short['items'] and top_artists_long['items']:
            recent_artists = set(a['name'] for a in top_artists_short['items'][:3])
            longtime_artists = set(a['name'] for a in top_artists_long['items'][:3])
            
            if recent_artists.isdisjoint(longtime_artists):
                context['trend_message'] = "Your music taste has evolved significantly recently!"
            elif recent_artists == longtime_artists:
                context['trend_message'] = "You've remained very consistent in your top artists over time."
            else:
                context['trend_message'] = "While some of your favorites have stayed consistent, you're also exploring new artists."
        
    except Exception as e:
        messages.error(request, f"Error retrieving Spotify data: {str(e)}")
        context = {
            'short_term': [],
            'medium_term': [],
            'long_term': [],
            'ranks': range(1, 11),
            'consistency_score': 0,
            'short_term_labels': '[]',
            'short_term_values': '[]',
            'medium_term_labels': '[]',
            'medium_term_values': '[]',
            'long_term_labels': '[]',
            'long_term_values': '[]',
        }
    
    return render(request, 'visualization/time_comparison.html', context)


@spotify_login_required
def export_data(request):
    """View for exporting data"""
    # Get the token info from the session
    token_info = request.session.get('spotify_token_info')
    
    # If there's no token info, redirect to login
    if not token_info:
        messages.error(request, "You are not connected to Spotify. Please connect your account.")
        return redirect('spotify_login')
    
    # Create the SpotifyOAuth object
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
    
    # Use the custom Spotify client
    sp = create_spotify_client(token_info['access_token'])
    
    # Check if export is requested
    export_type = request.GET.get('type')
    export_format = request.GET.get('format')
    
    # If export is requested, handle it
    if export_type and export_format:
        try:
            # Handle different export types
            if export_type == 'top_tracks':
                return export_top_tracks(request, sp, export_format)
            elif export_type == 'audio_features':
                return export_audio_features(request, sp, export_format)
            elif export_type == 'genre_distribution':
                return export_genre_distribution(request, sp, export_format)
            elif export_type == 'recently_played':
                return export_recently_played(request, sp, export_format)
            elif export_type == 'artist_analysis':
                return export_artist_analysis(request, sp, export_format)
            elif export_type == 'playlists':
                return export_playlists(request, sp, export_format)
            else:
                messages.error(request, f"Export type '{export_type}' is not supported.")
                return redirect('export_data')
        except Exception as e:
            messages.error(request, f"Error exporting data: {str(e)}")
            logging.error(f"Export error: {str(e)}", exc_info=True)
            return redirect('export_data')
    
    # Create the context
    context = {
        'user_profile': sp.current_user(),
    }
    
    return render(request, 'visualization/export_data.html', context)


# Export Helper Functions
def export_top_tracks(request, sp, export_format):
    """
    Export the user's top tracks in the specified format
    """
    # Get time range from request, default to medium_term
    time_range = request.GET.get('time_range', 'medium_term')
    
    # Get the user's top tracks - limit 50 for more comprehensive data
    top_tracks = sp.current_user_top_tracks(limit=50, time_range=time_range)
    
    # Prepare data for export
    tracks_data = []
    for i, track in enumerate(top_tracks['items'], 1):
        # Get audio features for this track
        try:
            audio_features = sp.audio_features(track['id'])[0] or {}
        except:
            # If audio features not available, use an empty dict
            audio_features = {}
        
        # Prepare track data
        track_data = {
            'rank': i,
            'name': track['name'],
            'artist': ', '.join(artist['name'] for artist in track['artists']),
            'album': track['album']['name'],
            'release_date': track['album'].get('release_date', 'N/A'),
            'popularity': track['popularity'],
            'duration_ms': track['duration_ms'],
            'explicit': track['explicit'],
            'preview_url': track['preview_url'] or 'N/A',
            'spotify_url': track['external_urls'].get('spotify', 'N/A'),
            # Add some audio features if available
            'danceability': audio_features.get('danceability', 'N/A'),
            'energy': audio_features.get('energy', 'N/A'),
            'tempo': audio_features.get('tempo', 'N/A'),
            'valence': audio_features.get('valence', 'N/A'),
        }
        tracks_data.append(track_data)
    
    # Format filename with date and time range
    date_str = datetime.now().strftime('%Y%m%d')
    time_range_name = {
        'short_term': 'Last4Weeks', 
        'medium_term': 'Last6Months', 
        'long_term': 'AllTime'
    }.get(time_range, 'CustomRange')
    
    filename = f"TopTracks_{time_range_name}_{date_str}"
    
    # Export in the requested format
    if export_format == 'csv':
        return export_as_csv(tracks_data, filename)
    elif export_format == 'json':
        return export_as_json(tracks_data, filename)
    elif export_format == 'pdf':
        title = f"Your Top Tracks ({time_range_name})"
        description = "This report shows your most played tracks on Spotify based on your listening history."
        return export_as_pdf(tracks_data, filename, title, description)
    else:
        messages.error(request, f"Export format '{export_format}' is not supported for top tracks.")
        return redirect('export_data')

def export_audio_features(request, sp, export_format):
    """
    Export audio features of the user's top tracks
    """
    # Get time range from request, default to medium_term
    time_range = request.GET.get('time_range', 'medium_term')
    
    # Get the user's top tracks - limit 50 for comprehensive data
    top_tracks = sp.current_user_top_tracks(limit=50, time_range=time_range)
    
    # Get track IDs
    track_ids = [track['id'] for track in top_tracks['items']]
    
    # Get audio features for all tracks at once (in batches of 100 as per API limit)
    audio_features_data = []
    
    # Process in batches of 100 (Spotify API limit)
    for i in range(0, len(track_ids), 100):
        batch_ids = track_ids[i:i+100]
        try:
            batch_features = sp.audio_features(batch_ids)
            if batch_features:
                audio_features_data.extend(batch_features)
        except Exception as e:
            logging.error(f"Error fetching audio features: {str(e)}")
    
    # Prepare data for export by combining track info with audio features
    features_data = []
    
    for i, track in enumerate(top_tracks['items']):
        # Find matching audio features
        track_features = next((f for f in audio_features_data if f and f.get('id') == track['id']), {})
        
        # Prepare data for this track
        feature_item = {
            'rank': i + 1,
            'track_name': track['name'],
            'artist': ', '.join(artist['name'] for artist in track['artists']),
            'album': track['album']['name'],
            'popularity': track['popularity'],
            
            # Audio features
            'danceability': track_features.get('danceability', 'N/A'),
            'energy': track_features.get('energy', 'N/A'),
            'key': track_features.get('key', 'N/A'),
            'loudness': track_features.get('loudness', 'N/A'),
            'mode': track_features.get('mode', 'N/A'),
            'speechiness': track_features.get('speechiness', 'N/A'),
            'acousticness': track_features.get('acousticness', 'N/A'),
            'instrumentalness': track_features.get('instrumentalness', 'N/A'),
            'liveness': track_features.get('liveness', 'N/A'),
            'valence': track_features.get('valence', 'N/A'),
            'tempo': track_features.get('tempo', 'N/A'),
            'time_signature': track_features.get('time_signature', 'N/A'),
        }
        features_data.append(feature_item)
    
    # Format filename with date and time range
    date_str = datetime.now().strftime('%Y%m%d')
    time_range_name = {
        'short_term': 'Last4Weeks', 
        'medium_term': 'Last6Months', 
        'long_term': 'AllTime'
    }.get(time_range, 'CustomRange')
    
    filename = f"AudioFeatures_{time_range_name}_{date_str}"
    
    # Export in the requested format
    if export_format == 'csv':
        return export_as_csv(features_data, filename)
    elif export_format == 'json':
        return export_as_json(features_data, filename)
    elif export_format == 'xlsx':
        return export_as_excel(features_data, filename)
    elif export_format == 'pdf':
        title = f"Audio Features Analysis ({time_range_name})"
        description = "This report shows the audio characteristics of your top tracks on Spotify."
        return export_as_pdf(features_data, filename, title, description)
    else:
        messages.error(request, f"Export format '{export_format}' is not supported for audio features.")
        return redirect('export_data')

def export_genre_distribution(request, sp, export_format):
    """
    Export the user's genre distribution data
    """
    # Get the user's top artists
    top_artists = sp.current_user_top_artists(limit=50, time_range='medium_term')
    
    # Extract genres
    genres = {}
    artists_by_genre = {}
    
    for artist in top_artists['items']:
        for genre in artist['genres']:
            if genre in genres:
                genres[genre] += 1
                artists_by_genre[genre].append(artist['name'])
            else:
                genres[genre] = 1
                artists_by_genre[genre] = [artist['name']]
    
    # Sort genres by count
    sorted_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)
    
    # Prepare data for export
    genre_data = []
    for i, (genre, count) in enumerate(sorted_genres, 1):
        total_artists = len(top_artists['items'])
        percentage = (count / total_artists) * 100
        
        genre_item = {
            'rank': i,
            'genre': genre,
            'count': count,
            'percentage': round(percentage, 2),
            'top_artists': ', '.join(artists_by_genre[genre][:3]),  # List top 3 artists
        }
        genre_data.append(genre_item)
    
    # Format filename with date
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"GenreDistribution_{date_str}"
    
    # Export in the requested format
    if export_format == 'csv':
        return export_as_csv(genre_data, filename)
    elif export_format == 'json':
        return export_as_json(genre_data, filename)
    elif export_format == 'svg' or export_format == 'png':
        # Create a pie chart
        return export_genre_chart(genre_data, filename, export_format)
    elif export_format == 'pdf':
        title = "Your Genre Distribution"
        description = "This report shows the distribution of music genres in your listening history."
        return export_as_pdf(genre_data, filename, title, description)
    else:
        messages.error(request, f"Export format '{export_format}' is not supported for genre distribution.")
        return redirect('export_data')

def export_recently_played(request, sp, export_format):
    """
    Export the user's recently played tracks
    """
    # Get the user's recently played tracks (max limit is 50)
    recent_tracks = sp.current_user_recently_played(limit=50)
    
    # Prepare data for export
    tracks_data = []
    for i, item in enumerate(recent_tracks['items'], 1):
        track = item['track']
        played_at = item['played_at']  # ISO 8601 format
        
        # Convert played_at to a more readable format
        try:
            played_datetime = datetime.fromisoformat(played_at.replace('Z', '+00:00'))
            played_at_formatted = played_datetime.strftime('%Y-%m-%d %H:%M:%S')
        except:
            played_at_formatted = played_at
        
        track_data = {
            'position': i,
            'played_at': played_at_formatted,
            'track_name': track['name'],
            'artist': ', '.join(artist['name'] for artist in track['artists']),
            'album': track['album']['name'],
            'release_date': track['album'].get('release_date', 'N/A'),
            'duration_ms': track['duration_ms'],
            'popularity': track['popularity'],
            'explicit': track['explicit'],
            'spotify_url': track['external_urls'].get('spotify', 'N/A'),
        }
        tracks_data.append(track_data)
    
    # Format filename with date
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"RecentlyPlayed_{date_str}"
    
    # Export in the requested format
    if export_format == 'csv':
        return export_as_csv(tracks_data, filename)
    elif export_format == 'json':
        return export_as_json(tracks_data, filename)
    elif export_format == 'pdf':
        title = "Your Recently Played Tracks"
        description = "This report shows your most recently played tracks on Spotify with timestamps."
        return export_as_pdf(tracks_data, filename, title, description)
    else:
        messages.error(request, f"Export format '{export_format}' is not supported for recently played tracks.")
        return redirect('export_data')

def export_artist_analysis(request, sp, export_format):
    """
    Export analysis of the user's top artists
    """
    # Get time range from request, default to medium_term
    time_range = request.GET.get('time_range', 'medium_term')
    
    # Get the user's top artists
    top_artists = sp.current_user_top_artists(limit=50, time_range=time_range)
    
    # Prepare data for export
    artists_data = []
    
    for i, artist in enumerate(top_artists['items'], 1):
        # Get artist's genres
        genres = artist.get('genres', [])
        
        # Get related artists (up to 3)
        try:
            related = sp.artist_related_artists(artist['id'])
            related_artists = ', '.join([a['name'] for a in related['artists'][:3]])
        except:
            related_artists = 'N/A'
        
        artist_data = {
            'rank': i,
            'name': artist['name'],
            'popularity': artist['popularity'],
            'followers': artist['followers']['total'],
            'genres': ', '.join(genres) if genres else 'N/A',
            'related_artists': related_artists,
            'spotify_url': artist['external_urls'].get('spotify', 'N/A'),
        }
        artists_data.append(artist_data)
    
    # Format filename with date and time range
    date_str = datetime.now().strftime('%Y%m%d')
    time_range_name = {
        'short_term': 'Last4Weeks', 
        'medium_term': 'Last6Months', 
        'long_term': 'AllTime'
    }.get(time_range, 'CustomRange')
    
    filename = f"ArtistAnalysis_{time_range_name}_{date_str}"
    
    # Export in the requested format
    if export_format == 'csv':
        return export_as_csv(artists_data, filename)
    elif export_format == 'json':
        return export_as_json(artists_data, filename)
    elif export_format == 'pdf':
        title = f"Your Top Artists ({time_range_name})"
        description = "This report shows your most listened to artists on Spotify with genre information."
        return export_as_pdf(artists_data, filename, title, description)
    else:
        messages.error(request, f"Export format '{export_format}' is not supported for artist analysis.")
        return redirect('export_data')

def export_playlists(request, sp, export_format):
    """
    Export the user's playlists and their tracks
    """
    # Get user's playlists
    playlists = sp.current_user_playlists(limit=50)
    
    # Prepare data structure for export
    playlists_data = []
    
    for i, playlist in enumerate(playlists['items'], 1):
        # Basic playlist info
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        owner_name = playlist['owner']['display_name']
        track_count = playlist['tracks']['total']
        
        # Get up to 100 tracks from the playlist 
        # (limit to 100 to avoid very large exports and API rate limits)
        track_limit = min(100, track_count)
        
        try:
            tracks_response = sp.playlist_tracks(
                playlist_id, 
                limit=track_limit,
                fields='items(added_at,track(name,artists,album(name),duration_ms,popularity))'
            )
            
            # Process tracks
            tracks = []
            for j, item in enumerate(tracks_response['items'], 1):
                track = item.get('track')
                if not track:  # Skip if track is None (can happen with deleted tracks)
                    continue
                    
                # Format added_at date
                added_at = item.get('added_at', '')
                try:
                    added_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
                    added_at_formatted = added_datetime.strftime('%Y-%m-%d')
                except:
                    added_at_formatted = added_at
                
                # Calculate track duration in minutes and seconds
                duration_ms = track.get('duration_ms', 0)
                minutes = duration_ms // 60000
                seconds = (duration_ms % 60000) // 1000
                duration_formatted = f"{minutes}:{seconds:02d}"
                
                track_data = {
                    'position': j,
                    'name': track.get('name', 'Unknown'),
                    'artist': ', '.join(artist['name'] for artist in track.get('artists', [])),
                    'album': track.get('album', {}).get('name', 'Unknown'),
                    'duration': duration_formatted,
                    'added_at': added_at_formatted,
                    'popularity': track.get('popularity', 0),
                }
                tracks.append(track_data)
            
            # Create playlist entry
            playlist_data = {
                'id': playlist_id,
                'name': playlist_name,
                'owner': owner_name,
                'description': playlist.get('description', ''),
                'public': playlist.get('public', False),
                'collaborative': playlist.get('collaborative', False),
                'total_tracks': track_count,
                'tracks_exported': len(tracks),
                'tracks': tracks,
                'spotify_url': playlist.get('external_urls', {}).get('spotify', 'N/A'),
            }
            playlists_data.append(playlist_data)
            
        except Exception as e:
            logging.error(f"Error fetching tracks for playlist {playlist_name}: {str(e)}")
            # Add the playlist with error info
            playlist_data = {
                'id': playlist_id,
                'name': playlist_name,
                'owner': owner_name,
                'error': f"Could not fetch tracks: {str(e)}",
                'spotify_url': playlist.get('external_urls', {}).get('spotify', 'N/A'),
            }
            playlists_data.append(playlist_data)
    
    # Format filename with date
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"Playlists_{date_str}"
    
    # Export in the requested format
    if export_format == 'json':
        return export_as_json(playlists_data, filename)
    elif export_format == 'csv':
        # Flatten the nested tracks for CSV export
        flattened_data = []
        for playlist in playlists_data:
            playlist_info = {
                'playlist_id': playlist['id'],
                'playlist_name': playlist['name'],
                'owner': playlist['owner'],
                'description': playlist.get('description', ''),
                'public': playlist.get('public', False),
                'collaborative': playlist.get('collaborative', False),
                'total_tracks': playlist.get('total_tracks', 0),
            }
            
            # Add tracks if available
            if 'tracks' in playlist and playlist['tracks']:
                for track in playlist['tracks']:
                    track_info = playlist_info.copy()
                    track_info.update(track)
                    flattened_data.append(track_info)
            else:
                # Add just the playlist info if no tracks
                flattened_data.append(playlist_info)
        
        return export_as_csv(flattened_data, filename)
    elif export_format == 'pdf':
        title = "Your Spotify Playlists"
        description = "This report contains information about your Spotify playlists and their tracks."
        return export_as_pdf(playlists_data, filename, title, description, is_playlist=True)
    else:
        messages.error(request, f"Export format '{export_format}' is not supported for playlists.")
        return redirect('export_data')

# Helper functions for different export formats
def export_as_csv(data, filename):
    """Export data as a CSV file"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    if not data:
        response.write('No data available')
        return response
    
    # Extract field names from the first item
    fieldnames = data[0].keys()
    
    writer = csv.DictWriter(response, fieldnames=fieldnames)
    writer.writeheader()
    
    for item in data:
        writer.writerow(item)
    
    return response

def export_as_json(data, filename):
    """Export data as a JSON file"""
    response = HttpResponse(json.dumps(data, indent=4), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
    return response

def export_as_excel(data, filename):
    """Export data as an Excel file"""
    # Create Excel file in memory
    output = io.BytesIO()
    
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Write to Excel
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Data')
    
    # Set up response
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    
    return response

def export_as_pdf(data, filename, title, description, is_playlist=False):
    """Export data as a PDF file"""
    # Create a BytesIO buffer to receive the PDF data
    buffer = BytesIO()
    
    # Create the PDF object using the BytesIO buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Container for the 'Flowable' objects (paragraphs, tables, etc.)
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        spaceAfter=12,
    )
    
    # Add title and description
    elements.append(Paragraph(title, title_style))
    elements.append(Paragraph(description, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Add generation timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elements.append(Paragraph(f"Generated on: {timestamp}", styles['Italic']))
    elements.append(Spacer(1, 12))
    
    # Special handling for playlists due to nested structure
    if is_playlist:
        for playlist in data:
            # Add playlist header
            playlist_title = f"{playlist['name']} (by {playlist['owner']})"
            elements.append(Paragraph(playlist_title, styles['Heading2']))
            
            # Add playlist details
            playlist_details = [
                f"Description: {playlist.get('description', 'N/A')}",
                f"Total Tracks: {playlist.get('total_tracks', 0)}",
                f"Public: {'Yes' if playlist.get('public', False) else 'No'}",
                f"Collaborative: {'Yes' if playlist.get('collaborative', False) else 'No'}",
                f"Spotify URL: {playlist.get('spotify_url', 'N/A')}"
            ]
            for detail in playlist_details:
                elements.append(Paragraph(detail, styles['Normal']))
            
            # Add tracks table if tracks exist
            if 'tracks' in playlist and playlist['tracks']:
                elements.append(Spacer(1, 12))
                elements.append(Paragraph("Tracks:", styles['Heading3']))
                
                # Create table data starting with headers
                track_data = [['#', 'Track', 'Artist', 'Album', 'Duration', 'Added']]
                
                # Add track rows (limit to first 50 to avoid huge PDFs)
                for track in playlist['tracks'][:50]:
                    track_data.append([
                        str(track.get('position', '')),
                        track.get('name', 'Unknown'),
                        track.get('artist', 'Unknown'),
                        track.get('album', 'Unknown'),
                        track.get('duration', ''),
                        track.get('added_at', '')
                    ])
                
                # Create table
                track_table = Table(track_data)
                track_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(track_table)
            
            # Add separator between playlists
            elements.append(Spacer(1, 20))
    else:
        # Standard table for non-playlist data
        if data:
            # Create table data starting with headers
            table_data = [[k.replace('_', ' ').title() for k in data[0].keys()]]
            
            # Add rows
            for item in data:
                row = []
                for k, v in item.items():
                    # Convert any non-string values to strings
                    if not isinstance(v, str):
                        v = str(v)
                    # Truncate very long strings
                    if len(v) > 50:
                        v = v[:47] + '...'
                    row.append(v)
                table_data.append(row)
            
            # Create table
            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response with PDF as attachment
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    response.write(pdf)
    
    return response

def export_genre_chart(genre_data, filename, format):
    """Export genre distribution as a chart image"""
    # Create a figure with a specific size
    plt.figure(figsize=(10, 8))
    
    # Get top genres (limit to top 10 for better readability)
    top_genres = genre_data[:10]
    
    # Extract labels and values
    labels = [item['genre'] for item in top_genres]
    values = [item['percentage'] for item in top_genres]
    
    # Create pie chart
    plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, shadow=False)
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular
    
    # Add title
    plt.title('Your Genre Distribution (Top 10)', fontsize=16)
    
    # Save to a BytesIO object
    img_data = BytesIO()
    if format == 'svg':
        plt.savefig(img_data, format='svg', bbox_inches='tight')
        mimetype = 'image/svg+xml'
        file_ext = 'svg'
    else:  # Default to PNG
        plt.savefig(img_data, format='png', dpi=300, bbox_inches='tight')
        mimetype = 'image/png'
        file_ext = 'png'
    
    plt.close()
    
    # Create the response
    img_data.seek(0)
    response = HttpResponse(img_data, content_type=mimetype)
    response['Content-Disposition'] = f'attachment; filename="{filename}.{file_ext}"'
    
    return response
