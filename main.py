import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from dotenv import load_dotenv

load_dotenv()

# Spotify API credentials
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Authenticate with Spotify
scope = "playlist-modify-public"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=scope))

# Function to extract song metadata (title, artist) from MP3 files
def extract_metadata(file_path):
    try:
        audio = MP3(file_path, ID3=EasyID3)
        title = audio['title'][0]
        artist = audio['artist'][0]
        return title, artist
    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")
        return None, None

# Function to search for a song on Spotify
def search_spotify(title, artist):
    query = f"track:{title} artist:{artist}"
    results = sp.search(q=query, type='track', limit=1)
    tracks = results['tracks']['items']
    if tracks:
        return tracks[0]['id']
    return None

# Function to find an existing playlist by name
def find_existing_playlist(playlist_name):
    user_id = sp.me()['id']
    playlists = sp.user_playlists(user=user_id)
    
    for playlist in playlists['items']:
        if playlist['name'] == playlist_name:
            return playlist['id']
    
    return None

# Function to create or get the playlist by name
def create_or_get_spotify_playlist(playlist_name):
    # Check if the playlist exists
    playlist_id = find_existing_playlist(playlist_name)
    
    if playlist_id:
        print(f"Playlist '{playlist_name}' already exists. Adding songs to it.")
        return playlist_id
    else:
        # If it doesn't exist, create a new one
        print(f"Creating new playlist '{playlist_name}'.")
        user_id = sp.me()['id']
        playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
        return playlist['id']

# Function to add songs to the Spotify playlist
def add_tracks_to_playlist(playlist_id, track_ids):
    if track_ids:
        sp.playlist_add_items(playlist_id, track_ids)

# Main function to convert offline playlist into Spotify playlist
def convert_offline_to_spotify(offline_folder, playlist_name):
    track_ids = []
    
    for root, dirs, files in os.walk(offline_folder):
        for file in files:
            if file.endswith(".mp3"):  # You can add support for other formats
                file_path = os.path.join(root, file)
                title, artist = extract_metadata(file_path)
                
                if title and artist:
                    print(f"Searching Spotify for '{title}' by '{artist}'...")
                    track_id = search_spotify(title, artist)
                    
                    if track_id:
                        track_ids.append(track_id)
                        print(f"Added '{title}' by '{artist}' to the playlist.")
                    else:
                        print(f"Could not find '{title}' by '{artist}' on Spotify.")
    
    if track_ids:
        playlist_id = create_or_get_spotify_playlist(playlist_name)
        add_tracks_to_playlist(playlist_id, track_ids)
        print(f"Playlist '{playlist_name}' updated with {len(track_ids)} songs.")
    else:
        print("No songs found on Spotify.")

# Example usage
offline_folder = "/path/to/your/music/folder"
playlist_name = "My Spotify Playlist"
convert_offline_to_spotify(offline_folder, playlist_name)