from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('personal-insights/', views.personal_insights, name='personal_insights'),
    path('public-trends/', views.public_trends, name='public_trends'),
    path('artist/<str:artist_id>/', views.artist_analysis, name='artist_analysis'),
    path('track/<str:track_id>/', views.track_analysis, name='track_analysis'),
] 