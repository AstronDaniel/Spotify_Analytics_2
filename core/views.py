from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import spotipy
from users.spotify_utils import CustomSpotifyOAuth


def home(request):
    """View for the home page"""
    return render(request, 'core/home.html')


def about(request):
    """View for the about page"""
    return render(request, 'core/about.html')


def contact(request):
    """View for the contact page"""
    return render(request, 'core/contact.html')


def privacy(request):
    """View for the privacy policy page"""
    return render(request, 'core/privacy.html')


def terms(request):
    """View for the terms of service page"""
    return render(request, 'core/terms.html')


def error_404(request, exception):
    """Custom 404 error page"""
    return render(request, 'core/404.html', status=404)


def error_500(request):
    """Custom 500 error page"""
    return render(request, 'core/500.html', status=500)
