import os
import re
import time
import json
import base64
import requests
from dotenv import load_dotenv
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from unidecode import unidecode

# Load environment variables
load_dotenv()

# Constants
ALLOWED_EXTENSIONS = (".mp3",)

# Initialize Spotipy
def initialize_spotify():
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="playlist-modify-public"
    ))
    return sp, sp.current_user()["id"]

# Metadata extraction functions
def extract_metadata(file_path):
    try:
        audio = MP3(file_path, ID3=EasyID3)
        title = audio.get("title", [None])[0]
        artist = audio.get("artist", [None])[0]
        return unidecode(artist) if artist else None, unidecode(title) if title else None
    except Exception as e:
        print(f"Error extracting metadata: {e}")
        return None, None

def clean_filename(filename):
    name = os.path.splitext(filename)[0]
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\[.*?\]', '', name)
    name = name.replace("_", " ").strip()
    return unidecode(name)

def guess_metadata_from_filename(filename):
    name = clean_filename(filename)
    parts = name.split(" - ")
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return None, name.strip()

# Spotify helpers
def get_or_create_playlist(sp, user_id, playlist_name):
    try:
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
    except Exception as e:
        print(f"Error in get_or_create_playlist: {e}")
        return None

def search_track(sp, artist, title):
    def perform_search(artist_query, title_query):
        query = f"track:{title_query} artist:{artist_query}" if artist_query else title_query
        try:
            result = sp.search(q=query, limit=1, type='track')
            tracks = result.get("tracks", {}).get("items", [])
            if tracks:
                return tracks[0]["id"]
        except Exception as e:
            print(f"❌ Error searching for '{title_query}' by '{artist_query}': {e}")
            return None

    track_id = perform_search(artist, title)
    if track_id:
        return track_id

    if artist and "feat." in artist.lower():
        primary_artist = artist.split("feat.")[0].strip()
        track_id = perform_search(primary_artist, title)
        if track_id:
            return track_id

    return perform_search(None, title)

def add_tracks_to_playlist(sp, playlist_id, track_ids):
    try:
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            sp.playlist_add_items(playlist_id=playlist_id, items=batch)
            time.sleep(0.5)  # Avoid rate limit
    except Exception as e:
        print(f"⚠️ Failed to add tracks to playlist: {e}")

# Step 1: Get Access Token for data extraction
def get_access_token(client_id, client_secret):
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    }
    data = {'grant_type': 'client_credentials'}

    response = requests.post(url, headers=headers, data=data)

    print(f"Response Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")

    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Failed to get access token: {response.status_code} {response.text}")

# Step 2: Fetch data about a song
def get_track_info(access_token, track_id):
    url = f'https://api.spotify.com/v1/tracks/{track_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to get track info: {response.status_code}")

# Function to get the number of artist followers
def get_artist_followers(access_token, artist_name):
    url = f'https://api.spotify.com/v1/search?q={artist_name}&type=artist'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        artists = response.json().get('artists', {}).get('items', [])
        if artists:
            return artists[0]['followers']['total']
    return 0

# Save track info to a single JSON file
def save_track_info_to_json(track_infos, filename='track_info.json'):
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(track_infos, jsonfile, indent=4, ensure_ascii=False)

# Terminal folder picker
def prompt_for_folder():
    print("\n💡 TIP: How to find your folder path")
    print("  - macOS: Drag the folder into Terminal to paste its path")
    print("  - Windows: Shift + right-click folder > 'Copy as path'")
    print("  - Linux: Right-click > Properties or drag to Terminal")

    while True:
        path = input("📂 Enter full folder path: ").strip()
        if os.path.isdir(path):
            return path
        print(f"❌ Path does not exist: {path}\nPlease try again.\n")

# Main workflow
def convert_folder_to_playlist(sp, user_id, folder_path, playlist_name, walk_subfolders=False, extract_data=False):
    track_ids = []
    track_infos = []
    iterator = os.walk(folder_path) if walk_subfolders else [(folder_path, [], os.listdir(folder_path))]

    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

    try:
        access_token = get_access_token(client_id, client_secret)
    except Exception as e:
        print(e)
        return

    for root, _, files in iterator:
        for file in files:
            if file.lower().endswith(ALLOWED_EXTENSIONS):
                full_path = os.path.join(root, file)
                artist, title = extract_metadata(full_path)

                if not title:
                    artist, title = guess_metadata_from_filename(file)

                if title:
                    print(f"🔍 Searching Spotify for: {title} by {artist or 'Unknown'}")
                    track_id = search_track(sp, artist, title)
                    if track_id:
                        track_ids.append(track_id)
                        print(f"✅ Found and added: {file}")
                        if extract_data:
                            track_info = get_track_info(access_token, track_id)
                            if artist:
                                followers = get_artist_followers(access_token, artist)
                                track_info['artist_followers'] = followers
                            track_infos.append(track_info)
                    else:
                        print(f"❌ Not found: {file}")
                else:
                    print(f"⚠️ Could not extract title from: {file}")

    if track_ids:
        playlist_id = get_or_create_playlist(sp, user_id, playlist_name)
        if playlist_id:
            add_tracks_to_playlist(sp, playlist_id, track_ids)
            print(f"\n🎵 Done! {len(track_ids)} songs added to '{playlist_name}'.")

    if extract_data and track_infos:
        save_track_info_to_json(track_infos)
        print(f"Track information saved to track_info.json")
    elif not track_ids:
        print("\n😢 No valid songs found to add.")

# Entry point
if __name__ == "__main__":
    sp, user_id = initialize_spotify()
    folder_path = prompt_for_folder()
    playlist_name = input("🎧 Enter Spotify playlist name: ").strip()

    # Ask for walking through subfolders
    while True:
        walk_input = input("🔁 Walk through subfolders? (yes/y/no/n): ").strip().lower()
        if walk_input in ['yes', 'y']:
            walk = True
            break
        elif walk_input in ['no', 'n']:
            walk = False
            break
        else:
            print("Invalid input. Please enter 'yes' or 'no' (or 'y'/'n').")

    # Ask for extracting data
    while True:
        extract_input = input("Do you want to extract data about the songs and save it to a JSON file? (yes/y/no/n): ").strip().lower()
        if extract_input in ['yes', 'y']:
            extract_data = True
            break
        elif extract_input in ['no', 'n']:
            extract_data = False
            break
        else:
            print("Invalid input. Please enter 'yes' or 'no' (or 'y'/'n').")

    convert_folder_to_playlist(sp, user_id, folder_path, playlist_name, walk, extract_data)
