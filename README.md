# Spotify Analytics Platform

A comprehensive analytics platform that provides deep insights into music preferences and listening patterns using the Spotify API.

## Features

- 📊 Music trend visualization
- 👤 Personal listening insights
- 🌐 Public music trends
- 📱 Responsive design
- 📈 Detailed audio feature analysis
- 🎨 Genre distribution analysis
- 🎸 Artist popularity metrics
- 🔄 Real-time data processing
- 📤 Export and sharing capabilities
- 🎵 Song playback integration

## User Requirements

- Access music trends without login (visitor access)
- Authenticate via Spotify account for personalized analytics
- Analyze personal music preferences and listening patterns
- Compare music across different time periods (e.g., 90s music vs. current)
- Discover new music based on analytics insights
- Share music insights with friends and family
- Export analytics data in various formats

## Tech Stack

- **Backend**: Django, Python
- **Frontend**: HTML5, CSS3, JavaScript, jQuery
- **UI Frameworks**: Bootstrap 5
- **Data Visualization**: Chart.js, D3.js
- **API Integration**: Spotify Web API
- **Database**: PostgreSQL

## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file with your Spotify API credentials
6. Run migrations: `python manage.py migrate`
7. Start the development server: `python manage.py runserver`

## Project Structure

```
spotify_analytics/
├── core/                  # Django app for main functionality
├── users/                 # Django app for user authentication
├── analytics/             # Django app for data processing and analytics
├── visualization/         # Django app for charts and graphs
├── static/                # Static files (CSS, JS, images)
├── templates/             # HTML templates
├── manage.py              # Django management script
└── requirements.txt       # Project dependencies
```

## Spotify API Integration

This platform uses the Spotify Web API to fetch user data, including:
- Recently played tracks
- Top artists and tracks
- Saved albums and playlists
- Audio features and analysis
- Public music trends and statistics

## License

MIT 