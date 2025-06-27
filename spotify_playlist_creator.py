import os
import re
import time
from dotenv import load_dotenv
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from unidecode import unidecode

# === LOAD ENVIRONMENT VARIABLES ===
load_dotenv()
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
ALLOWED_EXTENSIONS = (".mp3",)  # Only MP3 files are allowed

# === INIT SPOTIPY ===
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="playlist-modify-public"
))
user_id = sp.current_user()["id"]

# === METADATA EXTRACTION ===
def extract_metadata(file_path):
    try:
        audio = MP3(file_path, ID3=EasyID3)
        title = audio.get("title", [None])[0]
        artist = audio.get("artist", [None])[0]
        return unidecode(artist) if artist else None, unidecode(title) if title else None
    except Exception:
        return None, None

def clean_filename(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r'\(.*?\)', '', name)
    name = name.replace("_", " ").strip()
    return unidecode(name)

def guess_metadata_from_filename(filename):
    name = clean_filename(filename)
    parts = name.split(" - ")
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, name.strip()

# === SPOTIFY HELPERS ===
def get_or_create_playlist(playlist_name):
    playlists = sp.user_playlists(user=user_id)
    while playlists:
        for playlist in playlists['items']:
            if unidecode(playlist['name'].lower()) == unidecode(playlist_name.lower()):
                print(f"🎯 Found existing playlist: {playlist_name}")
                return playlist['id']
        if playlists['next']:
            playlists = sp.next(playlists)
        else:
            break
    print(f"🎉 Creating new playlist: {playlist_name}")
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
    return playlist['id']

def search_track(artist, title):
    query = f"track:{title} artist:{artist}" if artist else title
    try:
        result = sp.search(q=query, limit=1, type='track')
        tracks = result.get("tracks", {}).get("items", [])
        if tracks:
            return tracks[0]["id"]
    except Exception as e:
        print(f"❌ Error searching for '{title}' by '{artist}': {e}")
    return None

def add_tracks_to_playlist(playlist_id, track_ids):
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        try:
            sp.playlist_add_items(playlist_id=playlist_id, items=batch)
            time.sleep(0.5)  # avoid rate limit
        except Exception as e:
            print(f"⚠️ Failed to add batch {i}-{i+100}: {e}")

# === TERMINAL FOLDER PICKER ===
def prompt_for_folder():
    print("\n💡 TIP: How to find your folder path")
    print("  - macOS: Drag the folder into Terminal to paste its path")
    print("  - Windows: Shift + right-click folder > 'Copy as path'")
    print("  - Linux: Right-click > Properties or drag to Terminal")

    while True:
        path = input("📂 Enter full folder path: ").strip()
        if os.path.isdir(path):
            return path
        else:
            print(f"❌ Path does not exist: {path}\nPlease try again.\n")

# === MAIN WORKFLOW ===
def convert_folder_to_playlist(folder_path, playlist_name, walk_subfolders=False):
    track_ids = []
    iterator = os.walk(folder_path) if walk_subfolders else [
        (folder_path, [], os.listdir(folder_path))
    ]

    for root, _, files in iterator:
        for file in files:
            if file.lower().endswith(ALLOWED_EXTENSIONS):
                full_path = os.path.join(root, file)
                artist, title = extract_metadata(full_path)

                if not title:
                    artist, title = guess_metadata_from_filename(file)

                if title:
                    print(f"🔍 Searching Spotify for: {title} by {artist or 'Unknown'}")
                    track_id = search_track(artist, title)
                    if track_id:
                        track_ids.append(track_id)
                        print(f"✅ Found and added: {file}")
                    else:
                        print(f"❌ Not found: {file}")
                else:
                    print(f"⚠️ Could not extract title from: {file}")

    if track_ids:
        playlist_id = get_or_create_playlist(playlist_name)
        add_tracks_to_playlist(playlist_id, track_ids)
        print(f"\n🎵 Done! {len(track_ids)} songs added to '{playlist_name}'.")
    else:
        print("\n😢 No valid songs found to add.")

# === ENTRY POINT ===
if __name__ == "__main__":
    folder_path = prompt_for_folder()
    playlist_name = input("🎧 Enter Spotify playlist name: ").strip()
    walk = input("🔁 Walk through subfolders? (yes/no): ").strip().lower() == "yes"
    convert_folder_to_playlist(folder_path, playlist_name, walk)
