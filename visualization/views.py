from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
import spotipy
import json
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
        
        # Prepare data for visualization
        short_term_data = {artist['name']: i for i, artist in enumerate(top_artists_short['items'], 1)}
        medium_term_data = {artist['name']: i for i, artist in enumerate(top_artists_medium['items'], 1)}
        long_term_data = {artist['name']: i for i, artist in enumerate(top_artists_long['items'], 1)}
        
        # Calculate consistency score - how many artists are shared across time periods
        all_artists = set()
        for artist in top_artists_short['items']:
            all_artists.add(artist['name'])
        for artist in top_artists_medium['items']:
            all_artists.add(artist['name'])
        for artist in top_artists_long['items']:
            all_artists.add(artist['name'])
            
        short_term_set = {artist['name'] for artist in top_artists_short['items']}
        medium_term_set = {artist['name'] for artist in top_artists_medium['items']}
        long_term_set = {artist['name'] for artist in top_artists_long['items']}
        
        shared_short_medium = len(short_term_set.intersection(medium_term_set))
        shared_short_long = len(short_term_set.intersection(long_term_set))
        shared_medium_long = len(medium_term_set.intersection(long_term_set))
        
        avg_shared = (shared_short_medium + shared_short_long + shared_medium_long) / 3
        consistency_score = int((avg_shared / 10) * 100) if top_artists_short['items'] else 0
        
        # Prepare chart data
        short_term_labels = json.dumps([artist['name'] for artist in top_artists_short['items'][:5]])
        short_term_values = json.dumps([artist.get('popularity', 0) for artist in top_artists_short['items'][:5]])
        
        medium_term_labels = json.dumps([artist['name'] for artist in top_artists_medium['items'][:5]])
        medium_term_values = json.dumps([artist.get('popularity', 0) for artist in top_artists_medium['items'][:5]])
        
        long_term_labels = json.dumps([artist['name'] for artist in top_artists_long['items'][:5]])
        long_term_values = json.dumps([artist.get('popularity', 0) for artist in top_artists_long['items'][:5]])
        
        # Create the context
        context = {
            'short_term': top_artists_short['items'],
            'medium_term': top_artists_medium['items'],
            'long_term': top_artists_long['items'],
            'ranks': range(1, 11),  # 1-10 for ranking
            'consistency_score': consistency_score,
            'short_term_labels': short_term_labels,
            'short_term_values': short_term_values,
            'medium_term_labels': medium_term_labels,
            'medium_term_values': medium_term_values,
            'long_term_labels': long_term_labels,
            'long_term_values': long_term_values,
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
            # This would be where we handle the actual export
            # For now, we'll just redirect back with a message
            messages.info(request, f"Export of {export_type} in {export_format} format is coming soon!")
            return redirect('export_data')
        except Exception as e:
            messages.error(request, f"Error exporting data: {str(e)}")
    
    # Create the context
    context = {
        'user_profile': sp.current_user(),
    }
    
    return render(request, 'visualization/export_data.html', context)
