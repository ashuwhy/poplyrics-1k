import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import lyricsgenius
import json
from dotenv import load_dotenv
import os
import logging
import re

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_tracks.log"),
        logging.StreamHandler()
    ]
)

# Spotipy API credentials
SPOTIPY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Genius API credentials
GENIUS_ACCESS_TOKEN = os.getenv('GENIUS_API_TOKEN')

# Initialize Spotify and Genius API clients
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID,
                                                                client_secret=SPOTIPY_CLIENT_SECRET))
genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)

# Function to fetch genres from Genius
def fetch_genres_from_genius(artist_name):
    # Placeholder for fetching genres from Genius
    # You might need to use another API or a different method to get genres
    return ["pop"]  # Default genre

# Function to clean lyrics
def clean_lyrics(lyrics, song_title):
    start_idx = lyrics.find('[')
    if start_idx != -1:
        lyrics = lyrics[start_idx:]
    else:
        logging.warning(f"Lyrics for song '{song_title}' do not contain session headers.")
        return lyrics.strip()

    lines = lyrics.split('\n')

    unwanted_languages = ['Trke', 'Español', 'Português', 'Italiano', 'Deutsch', 'Српски', 
                          'Franais', 'Türkçe', 'Ελληνικά', 'Français', 'فارسی', 'العربية']

    unwanted_promotions = [r'See .* LiveGet tickets as low as', r'You might also like']

    cleaned_lines = []
    for line in lines:
        if line.startswith('Translations') or any(lang in line for lang in unwanted_languages):
            continue
        if any(re.search(pattern, line) for pattern in unwanted_promotions):
            continue
        line = re.sub(r'\d+Embed', '', line)
        line = re.sub(r'\d+ Contributors', '', line)
        cleaned_lines.append(line)

    cleaned_lyrics = '\n'.join(cleaned_lines).strip()

    if not cleaned_lyrics.startswith('['):
        logging.warning(f"Lyrics for song '{song_title}' do not start with '[' after cleaning.")
        return lyrics.strip()

    unwanted_patterns = [r'^Top canciones de', r'^New Music Friday']
    if any(re.match(pattern, cleaned_lyrics, flags=re.IGNORECASE) for pattern in unwanted_patterns):
        logging.warning(f"Lyrics for song '{song_title}' contain unwanted content.")
        return lyrics.strip()

    if len(cleaned_lyrics) < 100:
        logging.warning(f"Lyrics for song '{song_title}' are too short after cleaning.")
        return lyrics.strip()

    return cleaned_lyrics

# Read defective tracks from the text file
defective_tracks = []
with open('defective_tracks.txt', 'r') as f:
    defective_tracks = f.readlines()

# Open the JSON file in write mode to start with an empty list
with open('fixed_tracks.json', 'w') as f:
    json.dump([], f)

# Iterate through each line in the file
for line in defective_tracks:
    # Strip whitespace and split by hyphen to get artist and track name
    parts = line.strip().split(' - ')
    if len(parts) == 2:
        artist_name = parts[0].strip()
        track_name = parts[1].strip()

        logging.info(f"Processing track: {track_name} by {artist_name}")

        try:
            # Fetch the track information from Spotify
            results = spotify.search(q=f"track:{track_name} artist:{artist_name}", type="track", limit=1)
            tracks = results['tracks']['items']

            if tracks:
                track = tracks[0]

                # Extract required information
                track_data = {
                    "track_name": track['name'],
                    "album": track['album']['name'],
                    "release_date": track['album']['release_date'],
                    "song_length": f"{int(track['duration_ms'] // 60000)}:{int((track['duration_ms'] % 60000) / 1000):02d}",
                    "popularity": track['popularity'],
                    "songwriters": [artist['name'] for artist in track['artists']],
                    "artist": track['artists'][0]['name']
                }

                # Fetch the lyrics from Genius
                song = genius.search_song(track_name, artist_name)
                if song:
                    logging.info(f"Genius URL: {song.url}")
                    track_data['lyrics'] = clean_lyrics(song.lyrics, track_name)
                else:
                    track_data['lyrics'] = "Lyrics not found."

                # Fetch genres from Genius
                track_data['genre'] = fetch_genres_from_genius(artist_name)

                # Append track data to the JSON file
                with open('fixed_tracks.json', 'r+') as f:
                    data = json.load(f)
                    data.append(track_data)
                    f.seek(0)
                    json.dump(data, f, indent=4)

                logging.info(f"Successfully processed and saved track: {track_name} by {artist_name}")
            else:
                logging.warning(f"Track not found on Spotify: {track_name} by {artist_name}")

        except Exception as e:
            logging.error(f"Error processing track '{track_name}' by '{artist_name}': {e}")
