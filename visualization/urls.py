from django.urls import path
from . import views

urlpatterns = [
    path('genre-distribution/', views.genre_distribution, name='genre_distribution'),
    path('audio-features/', views.audio_features, name='audio_features'),
    path('time-comparison/', views.time_comparison, name='time_comparison'),
    path('export-data/', views.export_data, name='export_data'),
] 