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
    
    # Extract top genres from the user's top artists
    genre_counts = {}
    for artist in top_artists['items']:
        for genre in artist['genres']:
            if genre in genre_counts:
                genre_counts[genre] += 1
            else:
                genre_counts[genre] = 1
    
    # Sort genres by count and get the top 3
    top_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_genres = [genre.title() for genre, count in top_genres] if top_genres else ['No genres found']
    
    # Create the context
    context = {
        'user_profile': user_profile,
        'recently_played': recently_played,
        'top_artists': top_artists,
        'top_tracks': top_tracks,
        'top_genres': top_genres,
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
    
    # Get recently played tracks
    recently_played = sp.current_user_recently_played(limit=50)
    
    # Get user profile
    user_profile = sp.current_user()
    
    # Generate real insights from the data
    insights = generate_insights(
        top_artists_short, top_artists_medium, top_artists_long,
        top_tracks_short, top_tracks_medium, top_tracks_long,
        recently_played
    )
    
    # Create the context
    context = {
        'top_artists_short': top_artists_short,
        'top_artists_medium': top_artists_medium,
        'top_artists_long': top_artists_long,
        'top_tracks_short': top_tracks_short,
        'top_tracks_medium': top_tracks_medium,
        'top_tracks_long': top_tracks_long,
        'recently_played': recently_played,
        'user_profile': user_profile,
        'insights': insights
    }
    
    return render(request, 'analytics/personal_insights.html', context)


def generate_insights(top_artists_short, top_artists_medium, top_artists_long,
                    top_tracks_short, top_tracks_medium, top_tracks_long, 
                    recently_played):
    """Generate meaningful insights from Spotify data"""
    insights = {}
    
    # 1. Analyze artist loyalty
    insights['artist_loyalty'] = analyze_artist_loyalty(top_artists_short, top_artists_medium, top_artists_long)
    
    # 2. Analyze genre evolution
    insights['genre_evolution'] = analyze_genre_evolution(top_artists_short, top_artists_medium, top_artists_long)
    
    # 3. Analyze listening schedule
    insights['listening_schedule'] = analyze_listening_schedule(recently_played)
    
    # 4. Analyze mood patterns
    insights['mood_patterns'] = analyze_mood_patterns(top_tracks_short)
    
    # 5. Analyze listening diversity
    insights['listening_diversity'] = analyze_listening_diversity(top_artists_short, top_tracks_short)
    
    # 6. Analyze discovery rate
    insights['discovery_rate'] = analyze_discovery_rate(top_artists_short, top_artists_medium)
    
    return insights


def analyze_artist_loyalty(top_artists_short, top_artists_medium, top_artists_long):
    """Analyze which artists the user has been loyal to across time periods"""
    
    # Extract artist names from each time period
    short_artists = [artist['name'] for artist in top_artists_short['items']]
    medium_artists = [artist['name'] for artist in top_artists_medium['items']]
    long_artists = [artist['name'] for artist in top_artists_long['items']]
    
    # Find artists that appear in all three time periods
    loyal_artists = [artist for artist in short_artists if artist in medium_artists and artist in long_artists]
    
    if loyal_artists:
        # Get the top loyal artist
        top_loyal_artist = loyal_artists[0]
        
        # Find the position in each time range
        short_pos = short_artists.index(top_loyal_artist) + 1 if top_loyal_artist in short_artists else 0
        medium_pos = medium_artists.index(top_loyal_artist) + 1 if top_loyal_artist in medium_artists else 0
        long_pos = long_artists.index(top_loyal_artist) + 1 if top_loyal_artist in long_artists else 0
        
        return {
            'has_loyal_artist': True,
            'artist': top_loyal_artist,
            'short_pos': short_pos,
            'medium_pos': medium_pos,
            'long_pos': long_pos,
            'all_loyal_artists': loyal_artists
        }
    else:
        # Check if there's at least consistency between medium and long term
        medium_long_loyal = [artist for artist in medium_artists if artist in long_artists]
        
        if medium_long_loyal:
            return {
                'has_loyal_artist': True,
                'artist': medium_long_loyal[0],
                'short_pos': 0,
                'medium_pos': medium_artists.index(medium_long_loyal[0]) + 1,
                'long_pos': long_artists.index(medium_long_loyal[0]) + 1,
                'all_loyal_artists': medium_long_loyal
            }
        else:
            return {
                'has_loyal_artist': False
            }


def analyze_genre_evolution(top_artists_short, top_artists_medium, top_artists_long):
    """Analyze how the user's genre preferences have evolved over time"""
    
    # Count genres for each time period
    short_genres = {}
    for artist in top_artists_short['items']:
        for genre in artist['genres']:
            short_genres[genre] = short_genres.get(genre, 0) + 1
    
    medium_genres = {}
    for artist in top_artists_medium['items']:
        for genre in artist['genres']:
            medium_genres[genre] = medium_genres.get(genre, 0) + 1
    
    # Find top genres for each period
    top_short_genres = sorted(short_genres.items(), key=lambda x: x[1], reverse=True)[:3]
    top_medium_genres = sorted(medium_genres.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Find genres that have increased or decreased
    changing_genres = []
    for genre, count in top_short_genres:
        if genre in medium_genres:
            medium_count = medium_genres[genre]
            percent_change = ((count - medium_count) / medium_count * 100) if medium_count > 0 else 100
            
            if abs(percent_change) >= 20:  # Only report significant changes
                changing_genres.append({
                    'name': genre,
                    'percent_change': round(percent_change),
                    'direction': 'increased' if percent_change > 0 else 'decreased'
                })
    
    # If we didn't find significant changes in top genres, look at new genres
    if not changing_genres:
        for genre, count in top_short_genres:
            if genre not in medium_genres:
                changing_genres.append({
                    'name': genre,
                    'percent_change': 100,
                    'direction': 'increased'
                })
    
    return {
        'top_short_genres': [g[0] for g in top_short_genres],
        'top_medium_genres': [g[0] for g in top_medium_genres],
        'changing_genres': changing_genres
    }


def analyze_listening_schedule(recently_played):
    """Analyze when the user listens to music most frequently"""
    
    if 'items' not in recently_played or not recently_played['items']:
        return {
            'has_data': False
        }
    
    # Track play counts by day and hour
    day_counts = {'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 
                 'Friday': 0, 'Saturday': 0, 'Sunday': 0}
    hour_counts = {h: 0 for h in range(24)}
    
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    for item in recently_played['items']:
        played_at = item['played_at']  # Format may include milliseconds: 2025-04-19T11:34:59.227Z
        # Convert to datetime, handling both with and without milliseconds
        from datetime import datetime
        try:
            # Try parsing with milliseconds
            played_at_dt = datetime.strptime(played_at, '%Y-%m-%dT%H:%M:%S.%fZ')
        except ValueError:
            try:
                # Try parsing without milliseconds
                played_at_dt = datetime.strptime(played_at, '%Y-%m-%dT%H:%M:%SZ')
            except ValueError:
                # Skip this item if we can't parse the date
                continue
        
        # Get day of week and hour
        day = weekdays[played_at_dt.weekday()]
        hour = played_at_dt.hour
        
        day_counts[day] += 1
        hour_counts[hour] += 1
    
    # Find most active day and time period
    most_active_day = max(day_counts.items(), key=lambda x: x[1])[0]
    
    # Group hours into periods
    periods = {
        'Morning (6am-12pm)': sum(hour_counts[h] for h in range(6, 12)),
        'Afternoon (12pm-5pm)': sum(hour_counts[h] for h in range(12, 17)),
        'Evening (5pm-9pm)': sum(hour_counts[h] for h in range(17, 21)),
        'Night (9pm-6am)': sum(hour_counts[h] for h in range(21, 24)) + sum(hour_counts[h] for h in range(0, 6))
    }
    
    most_active_period = max(periods.items(), key=lambda x: x[1])[0]
    
    return {
        'has_data': True,
        'most_active_day': most_active_day,
        'most_active_period': most_active_period,
        'day_counts': day_counts,
        'hour_counts': hour_counts
    }


def analyze_mood_patterns(top_tracks):
    """Analyze the mood patterns in the user's top tracks"""
    
    # This would ideally use the audio features API to get actual audio features
    # But for simplicity, we'll make some assumptions based on track names
    
    # Placeholder for a real analysis
    energy_mood = "energetic"
    secondary_mood = "upbeat"
    
    return {
        'primary_mood': energy_mood,
        'secondary_mood': secondary_mood
    }


def analyze_listening_diversity(top_artists, top_tracks):
    """Analyze how diverse the user's listening habits are"""
    
    # Count unique artists
    unique_artists = len(top_artists['items'])
    
    # Count unique genres
    all_genres = []
    for artist in top_artists['items']:
        all_genres.extend(artist['genres'])
    
    unique_genres = len(set(all_genres))
    
    # Determine diversity level
    if unique_genres > 15:
        diversity_level = "very diverse"
    elif unique_genres > 10:
        diversity_level = "diverse"
    elif unique_genres > 5:
        diversity_level = "somewhat diverse"
    else:
        diversity_level = "focused"
    
    return {
        'unique_artists': unique_artists,
        'unique_genres': unique_genres,
        'top_genre': set(all_genres).pop() if all_genres else "Unknown",
        'diversity_level': diversity_level
    }


def analyze_discovery_rate(top_artists_short, top_artists_medium):
    """Analyze how quickly the user discovers new artists"""
    
    # Extract artist names from each time period
    short_artists = [artist['name'] for artist in top_artists_short['items']]
    medium_artists = [artist['name'] for artist in top_artists_medium['items']]
    
    # Count new artists in short term that weren't in medium term
    new_artists = [artist for artist in short_artists if artist not in medium_artists]
    new_artist_count = len(new_artists)
    
    # Calculate percentage
    discovery_percentage = (new_artist_count / len(short_artists)) * 100 if short_artists else 0
    
    # Determine discovery level
    if discovery_percentage > 70:
        discovery_level = "very high"
    elif discovery_percentage > 50:
        discovery_level = "high"
    elif discovery_percentage > 30:
        discovery_level = "moderate"
    elif discovery_percentage > 10:
        discovery_level = "low"
    else:
        discovery_level = "very low"
    
    return {
        'new_artist_count': new_artist_count,
        'discovery_percentage': round(discovery_percentage),
        'discovery_level': discovery_level,
        'new_artists': new_artists[:3]  # First 3 new artists
    }


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
