from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import JsonResponse
import spotipy
from users.spotify_utils import CustomSpotifyOAuth
import json
from users.spotify_client_fix import create_spotify_client
from users.decorators import spotify_login_required


@spotify_login_required
def dashboard(request):
    """Dashboard view for authenticated users"""
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
    
    # Use our custom Spotify client
    sp = create_spotify_client(token_info['access_token'])
    
    # Get the user's profile
    user_profile = sp.current_user()
    
    # Get the user's recently played tracks
    recently_played = sp.current_user_recently_played(limit=10)
    
    # Get the user's top artists
    top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')
    
    # Get the user's top tracks
    top_tracks = sp.current_user_top_tracks(limit=10, time_range='medium_term')
    
    # Create the context
    context = {
        'user_profile': user_profile,
        'recently_played': recently_played,
        'top_artists': top_artists,
        'top_tracks': top_tracks,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@spotify_login_required
def personal_insights(request):
    """View for personal music insights"""
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
    
    # Use our custom Spotify client
    sp = create_spotify_client(token_info['access_token'])
    
    # Get the user's top artists for different time ranges
    top_artists_short = sp.current_user_top_artists(limit=10, time_range='short_term')
    top_artists_medium = sp.current_user_top_artists(limit=10, time_range='medium_term')
    top_artists_long = sp.current_user_top_artists(limit=10, time_range='long_term')
    
    # Get the user's top tracks for different time ranges
    top_tracks_short = sp.current_user_top_tracks(limit=10, time_range='short_term')
    top_tracks_medium = sp.current_user_top_tracks(limit=10, time_range='medium_term')
    top_tracks_long = sp.current_user_top_tracks(limit=10, time_range='long_term')
    
    # Create the context
    context = {
        'top_artists_short': top_artists_short,
        'top_artists_medium': top_artists_medium,
        'top_artists_long': top_artists_long,
        'top_tracks_short': top_tracks_short,
        'top_tracks_medium': top_tracks_medium,
        'top_tracks_long': top_tracks_long,
    }
    
    return render(request, 'analytics/personal_insights.html', context)


def public_trends(request):
    """View for public music trends (no login required)"""
    # Create a dummy context for now (in a real app, this would use public Spotify API data)
    context = {
        'trending_artists': [
            {'name': 'Taylor Swift', 'image_url': 'https://media.gettyimages.com/id/1987932445/photo/los-angeles-california-taylor-swift-attends-the-66th-grammy-awards-at-crypto-com-arena-on.jpg?s=612x612&w=0&k=20&c=eRk8I8Z8h6EcUqDZNSAi36VZssd0undZKhfwbS5DoZI='},
            {'name': 'Drake', 'image_url': 'https://media.gettyimages.com/id/1140667589/photo/us-rapper-drake-poses-in-the-press-room-during-the-2019-billboard-music-awards-at-the-mgm.jpg?s=612x612&w=0&k=20&c=-R5_rpogqfIQGp9eth47nr7c5Q_Ajqw1wOIWNPLItSo='},
            {'name': 'The Weeknd', 'image_url': 'https://media.gettyimages.com/id/1319709679/photo/los-angeles-california-in-this-image-released-on-may-23-the-weeknd-performs-for-the-2021.jpg?s=612x612&w=0&k=20&c=H5WZbtt3zR0jXn9Ef_RLrg0gPE3XMAlafxJ2VWBIVMw='},
            {'name': 'Bad Bunny', 'image_url': 'https://media.gettyimages.com/id/1727326653/photo/cleveland-ohio-bad-bunny-attends-the-2023-forbes-30-under-30-summit-at-cleveland-public.jpg?s=612x612&w=0&k=20&c=U_OQ2fGd2kB1gmtyWQ_E5H0C9E7eWncflm0J6AZVX58='},
            {'name': 'Billie Eilish', 'image_url': 'https://media.gettyimages.com/id/1530545899/photo/los-angeles-california-billie-eilish-attends-the-world-premiere-of-barbie-at-shrine.jpg?s=612x612&w=0&k=20&c=iKqhxalfGNEDpUVHYF8gDJ26P2jRLl-eOGlYi-YEyJ8='},
        ],
        'trending_tracks': [
            {'name': 'Blinding Lights', 'artist': 'The Weeknd', 'image_url': 'https://f4.bcbits.com/img/a2542331661_16.jpg'},
            {'name': 'Shape of You', 'artist': 'Ed Sheeran', 'image_url': 'https://f4.bcbits.com/img/a2164455285_16.jpg'},
            {'name': 'Dance Monkey', 'artist': 'Tones and I', 'image_url': 'https://f4.bcbits.com/img/a0409233474_16.jpg'},
            {'name': 'Someone You Loved', 'artist': 'Lewis Capaldi', 'image_url': 'https://f4.bcbits.com/img/a3707462850_16.jpg'},
            {'name': 'Believer', 'artist': 'Imagine Dragons', 'image_url': 'https://f4.bcbits.com/img/a1201483238_16.jpg'},
        ],
        'trending_genres': [
            {'name': 'Pop', 'count': 35},
            {'name': 'Hip Hop', 'count': 28},
            {'name': 'R&B', 'count': 18},
            {'name': 'Rock', 'count': 15},
            {'name': 'Electronic', 'count': 12},
        ],
    }
    
    return render(request, 'analytics/public_trends.html', context)


@spotify_login_required
def artist_analysis(request, artist_id):
    """View for detailed artist analysis"""
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
    
    # Use our custom Spotify client
    sp = create_spotify_client(token_info['access_token'])
    
    # Get the artist
    artist = sp.get(f'artists/{artist_id}')
    
    # Get the artist's top tracks
    top_tracks = sp.get(f'artists/{artist_id}/top-tracks?country=US')
    
    # Get the artist's albums
    albums = sp.get(f'artists/{artist_id}/albums?album_type=album&limit=10')
    
    # Get related artists
    related_artists = sp.get(f'artists/{artist_id}/related-artists')
    
    # Create the context
    context = {
        'artist': artist,
        'top_tracks': top_tracks,
        'albums': albums,
        'related_artists': related_artists,
    }
    
    return render(request, 'analytics/artist_analysis.html', context)


@spotify_login_required
def track_analysis(request, track_id):
    """View for detailed track analysis"""
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
    
    # Use our custom Spotify client
    sp = create_spotify_client(token_info['access_token'])
    
    # Get the track
    track = sp.get(f'tracks/{track_id}')
    
    # Get the audio features
    audio_features = sp.get(f'audio-features/{track_id}')
    
    # Get the artist
    artist_id = track['artists'][0]['id']
    artist = sp.get(f'artists/{artist_id}')
    
    # Get recommendations based on the track
    recommendations = sp.get(f'recommendations?seed_tracks={track_id}&limit=5')
    
    # Create the context
    context = {
        'track': track,
        'audio_features': audio_features,
        'artist': artist,
        'recommendations': recommendations,
    }
    
    return render(request, 'analytics/track_analysis.html', context)
