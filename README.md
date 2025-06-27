# Local Music to Spotify Playlist Creator — Terminal Edition

![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Spotipy](https://img.shields.io/badge/Spotipy-2.24.0-green.svg)
![Mutagen](https://img.shields.io/badge/Mutagen-1.47.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Disclaimer**: The majority of this project, including its code and documentation, was created with the assistance of Large Language Models (LLMs). These tools helped streamline development, generate code snippets, and draft documentation. While human oversight ensured quality and accuracy, LLMs played a significant role in the project's creation.

## Overview

Local Music to Spotify Playlist Creator is a Python application that allows users to convert their offline music collections into Spotify playlists. This enhanced **Terminal Edition** lets you turn your local music folder into a Spotify playlist directly from the terminal. It scans music files (like `.mp3`) for metadata or parses filenames, searches tracks on Spotify, and builds or updates your chosen playlist.

> 🛠️ No GUI required — this version is designed to run anywhere Python works.

## Features

- ✅ Scans local folders (with optional subfolder support)
- ✅ Extracts song title and artist information from local MP3 files using ID3 or filename guessing
- ✅ Searches for songs on Spotify using the Spotify Web API
- ✅ Automatically creates or updates a Spotify playlist
- ✅ Batches track uploads to handle large collections (up to 100 per call)
- ✅ User-friendly terminal interface with cross-platform folder tips
- ✅ User-friendly output indicating the status of each song added

## Prerequisites

Before using this tool, make sure you have:

- Python 3.13 or later installed
- A Spotify account (Free or Premium)
- Spotify Developer credentials from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- An active internet connection to search for songs on Spotify

## Installation

1. **Fork or clone the repository**:

   ```bash
   git clone https://github.com/yourusername/local-music-to-spotify-playlist-creator.git
   cd local-music-to-spotify-playlist-creator
   ```

2. **(Optional) Create a virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install required packages**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Add your Spotify credentials to a `.env` file**:

   ```env
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8000/callback
   ```

## Usage

1. **Run the script**:

   ```bash
   python spotify_playlist_creator.py
   ```

2. **Follow the prompts in your terminal**:

   - Choose a local folder (manually type or paste the full path, e.g., `/path/to/your/songs`)
   - Name the target Spotify playlist
   - Decide whether to scan subfolders
   - Authorize Spotify access in your browser (only once per session)


## Notes

- The application currently supports MP3 files. You can modify the code to support other formats if desired.
- Ensure that you have an active internet connection to search for songs on Spotify.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project is a fork and enhancement of the original [Local Music to Spotify Playlist Creator](https://github.com/xectrone/local-music-to-spotify-playlist-creator) by [xectrone](https://github.com/xectrone).
- [Spotipy](https://spotipy.readthedocs.io/en/2.19.0/) - A lightweight Python library for the Spotify Web API.
- [Mutagen](https://mutagen.readthedocs.io/en/latest/) - A Python module to handle audio metadata.