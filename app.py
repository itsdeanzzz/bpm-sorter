from flask import Flask, request, redirect, session, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

# Replace with your Spotify credentials
SPOTIPY_CLIENT_ID = '17aae4140a024ecb83f4ff9f026ef5fe'
SPOTIPY_CLIENT_SECRET = '7289b4b9932e4023872f47216eb32d84'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'

scope = "playlist-read-private playlist-modify-public playlist-modify-private"

sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=scope
)

@app.route('/')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect('/playlists')

@app.route('/playlists')
def playlists():
    sp = spotipy.Spotify(auth=session['token_info']['access_token'])
    user_playlists = sp.current_user_playlists()
    return render_template('index.html', playlists=user_playlists['items'])

@app.route('/sort/<playlist_id>', methods=['GET', 'POST'])
def sort_playlist(playlist_id):
    sp = spotipy.Spotify(auth=session['token_info']['access_token'])

    # Get filters from request
    min_bpm = float(request.args.get('min_bpm', 0))
    max_bpm = float(request.args.get('max_bpm', 1000))
    order = request.args.get('order', 'asc')

    results = sp.playlist_tracks(playlist_id)
    track_ids = [item['track']['id'] for item in results['items'] if item['track']]

    # Fetch audio features
    features = sp.audio_features(track_ids)
    track_info = [
        (f['tempo'], f['id']) for f in features if f and min_bpm <= f['tempo'] <= max_bpm
    ]
    track_info.sort(reverse=(order == 'desc'))

    sorted_tracks = [track_id for _, track_id in track_info]

    # Create new playlist
    user_id = sp.current_user()['id']
    playlist_name = f"Sorted BPM {min_bpm}-{max_bpm} ({order.upper()})"
    new_playlist = sp.user_playlist_create(user_id, playlist_name, public=False)
    sp.playlist_add_items(new_playlist['id'], sorted_tracks)

    return f"New sorted playlist created: <a href='{new_playlist['external_urls']['spotify']}' target='_blank'>Open Playlist</a>"

if __name__ == '__main__':
    app.run(debug=True)
