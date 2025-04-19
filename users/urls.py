from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('spotify-login/', views.spotify_login, name='spotify_login'),
    path('callback/', views.callback, name='callback'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout, name='logout'),
    path('delete-data/', views.delete_data, name='delete_data'),
    # Debug route - remove in production
    path('debug-spotify/', views.debug_spotify, name='debug_spotify'),
] 