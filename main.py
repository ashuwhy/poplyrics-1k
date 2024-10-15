import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from lyricsgenius import Genius
import re
import pandas as pd
from tqdm import tqdm
import time
import json
import logging
from huggingface_hub import create_repo, upload_file
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ReadTimeout, ConnectionError, HTTPError
from difflib import SequenceMatcher


# Load environment variables from a .env file (if using one)
load_dotenv()

# -------------------- Configuration --------------------

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    filename='dataset_builder.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Spotify API credentials from environment variables
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'your_spotify_client_id')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'your_spotify_client_secret')

# Genius API token from environment variables
GENIUS_API_TOKEN = os.getenv('GENIUS_API_TOKEN', 'your_genius_api_token')

# Musixmatch API key from environment variables
MUSIXMATCH_API_KEY = os.getenv('MUSIXMATCH_API_KEY', 'your_musixmatch_api_key')

# Hugging Face credentials from environment variables
HUGGINGFACE_USERNAME = os.getenv('HUGGINGFACE_USERNAME', 'your_username')
REPO_NAME = os.getenv('REPO_NAME', 'pop-lyrics-dataset')
HF_TOKEN = os.getenv('HF_TOKEN', 'your_hf_token')

# Spotify API rate limit parameters
SPOTIFY_MAX_RETRIES = 3
SPOTIFY_BACKOFF_FACTOR = 2  # Exponential backoff factor

# File paths
TOP_TRACKS_JSON = 'top_tracks.json'
DATASET_JSON = 'pop_lyrics_dataset.json'

# -------------------- Spotify API Setup --------------------

# Create a custom session with increased timeouts
session = requests.Session()

# Authenticate with Spotify using Client Credentials
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)
sp = spotipy.Spotify(
    client_credentials_manager=client_credentials_manager,
    requests_session=session,
    retries=SPOTIFY_MAX_RETRIES,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=SPOTIFY_BACKOFF_FACTOR,
    #timeout=(5, 30)  # (connect timeout, read timeout)
)

# -------------------- Genius API Setup --------------------

# Initialize Genius API
genius = Genius(
    GENIUS_API_TOKEN,
    timeout=15,
    retries=3,
    remove_section_headers=False,  # Retain session headers like [Chorus], [Verse 1], etc.
    skip_non_songs=False,
    excluded_terms=["(Remix)", "(Live)"]
)

# -------------------- Artists with Spotify IDs --------------------

artists_with_ids = {
    "Lady Gaga" : "1HY2Jd0NmPuamShAr6KMms",
    "Hayd" : "1adGvsK8A0XG2D18ufk7fZ",
    "Justin Bieber" : "1uNFoZAHBGtllmzznpCI3s",
    "The Kid LAROI" : "2tIP7SsRs7vjIcLrU85W8J",
    "Ed Sheeran" : "6eUKZXaKkcviH0Ku9w2n3V",
    "Charlie Puth" : "6VuMaDnrHyPL1p4EHjYLi7",
    "Shawn Mendes" : "7n2wHs1TKAczGzO7Dd2rGr",
    "JVKE" : "164Uj4eKjl6zTBKfJLFKKK",
    "Lauv" : "5JZ7CnR6gTvEMKX4g70Amv",
    "Stephen Sanchez" : "5XKFrudbV4IiuE5WuTPRmT",
    "Benson Boone" : "22wbnEMDvgVIAGdFeek6ET",
    "Harry Styles" : "6KImCVD70vtIoJWnq6nGn3",
    "Conan Gray" : "4Uc8Dsxct0oMqx0P6i60ea",
    "Chappell Roan" : "7GlBOeep6PqTfFi59PTUUN",
    "Halsey" : "26VFTg2z8YR0cCuwLzESi2",
    "Sabrina Carpenter" : "74KM79TiuVKeVCqs8QtB0B",
    "Taylor Swift" : "06HL4z0CvFAxyc27GXpf02",
    "Ariana Grande" : "66CXWjxzNUsdJxJ2JdwvnR",
    "Sasha Alex Sloan" : "4xnihxcoXWK3UqryOSnbw5",
    "Ali Gatie" : "4rTv3Ejc7hKMtmoBOK1B4T",
    "Bruno Mars" : "0du5cEVh5yTK9QJze8zA0C",
    "Dua Lipa" : "6M2wZ9GZgrQXHCFfjv46we",
    "Billie Eilish" : "6qqNVTkY8uBg9cP3Jd7DAH",
    "Katy Perry" : "6jJ0s89eD6GaHleKKya26X",
    "David Kushner" : "33NVpKoXjItPwUJTMZIOiY",
    "Myles Smith" : "3bO19AOone0ubCsfDXDtYt",
    "FINNEAS" : "37M5pPGs6V1fchFJSgCguX",
    "Post Malone" : "246dkjvS1zLTtiykXe5h60",
    "SZA" : "7tYKF4w9nC0nq9CsPZTHyP",
    "Hozier" : "2FXC3k01G6Gw61bmprjgqS",
    "The Weeknd" : "1Xyo4u8uXC1ZmMpatF05PJ",
    "Coldplay" : "4gzpq5DPGxSnKTe4SA8HAU",
    "Tate McRae" : "45dkTj5sMRSjrmBSBeiHym",
    "Frank Ocean" : "2h93pZq0e7k5yf4dywlkpM",
    "Alec Benjamin" : "5IH6FPUwQTxPSXurCrcIov",
    "Cigarettes After Sex" : "1QAJqy2dA3ihHBFIHRphZj",
    "Gracie Abrams" : "4tuJ0bMpJh08umKkEXKUI5",
    "Olivia Rodrigo" : "1McMsnEElThX1knmY4oliG",
    "Michael Jackson" : "3fMbdgg4jU18AjLCKBhRSm",
    "Future" : "1RyvyyTE3xzB2ZywiAwp0i",
    "Miley Cyrus" : "5YGY8feqx7naU7z4HrwZM6",
    "Doja Cat" : "5cj0lLjcoR7YOSnhnX0Po5",
    "Karol G" : "790FomKkXshlbRYZFtlgla",
    "Jimin" : "1oSPZhvZMIrWW5I41kPkkY",
    "Lana Del Rey" : "00FQb4jTyendYWaN8pK0wa",
    "Melanie Martinez" : "63yrD80RY3RNEM2YDpUpO8",
    "Jennifer Lopez" : "2DlGxzQSjYe5N6G9nkYghR",
    "Beyoncé" : "6vWDO969PvNqNYHIOW5v0m",
    "Madonna" : "6tbjWDEIzxoDsBA1FuhfPW",
    "Britney Spears" : "26dSoYclwsYLMAKD3tpOr4",
    "Justin Timberlake" : "31TPClRtHm23RisEBtV3X7",
    "Elton John" : "3PhoLpVuITZKcymswpck5b",
    "Celine Dion" : "4S9EykWXhStSc15wEx8QFK",
    "Prince" : "3MHaV05u0io8fQbZ2XPtlC",
    "The Beach Boys" : "3oDbviiivRWhXwIE8hxkVV",
    "Selena Gomez" : "0C8ZW7ezQVs4URX5aX7Kqx",
    "Janet Jackson" : "4qwGe91Bz9K2T8jXTZ815W",
    "Adele" : "1d4uM0g9449nE9TV5KeWch",
    "Backstreet Boys" : "5rSXSAkZ67PYJSvpUpkOr7",
    "Christina Aguilera" : "1l7ZsJRRS8wlW3WfJfPfNS",
    "Usher" : "23zg3TcAtWQy7J6upgbUnj",
    "The Jackson 5" : "2iE18Oxc8YSumAU232n4rW",
    "Pink" : "78rUTD7y6Cy67W1RVzYs7t",
    "Kelly Clarkson" : "3BmGtnKgCSGYIUhmivXKWX",
    "Jonas Brothers" : "7gOdHgIoIKoe4i9Tta6qdD",
    "The Black Eyed Peas" : "1yxSLGMDHlW21z4YXirZDS",
    "Spice Girls" : "0uq5PttqEjj3IH1bzwcrXF",
    "Cher" : "72OaDtakiy6yFqkt4TsiFt",
    "Shakira" : "0EmeFodog0BfCgMzAIvKQp",
    "Gwen Stefani" : "4yiQZ8tQPux8cPriYMWUFP",
    "'N Sync" : "6Ff53KvcvAj5U7Z1vojB5o",
    "Cyndi Lauper" : "2BTZIqw0ntH9MvilQ3ewNY",
    "The 1975" : "3mIj9lX2MWuHmhNCA7LSCW",
    "New Kids on the Block" : "55qiaow2sDYtjqu1mwRua6",
    "Demi Lovato" : "6S2OmqARrzebs0tKUEyXyp",
    "R. Kelly" : "3AuMNF8rQAKOzjYppFNAoB",
    "Nick Jonas" : "4Rxn7Im3LGfyRkY2FlHhWi",
    "Maroon 5" : "04gDigrS5kc9YWfZHwBETP",
    "Chris Brown" : "7bXgB6jMjp9ATFy66eO08Z",
    "Barry Manilow" : "3alW3LYQS8K29z8C8NSLIX",
    "One Direction" : "4AK6F7OLvEQ5QYCBNiQWHq",
    "GRAHAM" : "662lI9CXPZ0a6ou4CkLr0G",
    "Michael Bublé" : "1GxkXlMwML1oSg5eLPiAz3",
    "Susan Boyle" : "1qAuetfG6mhtDgsVIffWQc",
    "Smash Mouth" : "2iEvnFsWxR0Syqu2JNopAd",
    "Steely Dan" : "6P7H3ai06vU1sGvdpBwDmE",
    "Ashlee Simpson" : "4hqDqHtBlgxXpLXVYf7c8L",
    "WHAM!" : "5lpH0xAS4fVfLkACg9DAuM",
    "The Bangles" : "51l0uqRxGaczYr4271pVIC",
    "Harry Connick, Jr." : "6u17YlWtW4oqFF5Hn9UU79",
    "OneRepublic" : "5Pwc4xIPtQLFEnJriah9YJ",
    "Sam Smith" : "2wY79sveU1sp5g7SokKOiI",
    "Rick Astley" : "0gxyHStUsqpMadRV0Di1Qt",
    "Anne Murray" : "7d7q5Y1p2QWS4QRAhTQR5E",
    "Sia" : "5WUlDfRSoLAfcVSX1WnrxN",
    "Fiona Apple" : "3g2kUQ6tHLLbmkV7T4GPtL",
    "Kylie Minogue" : "4RVnAU35WRWra6OZ3CbbMA",
    "Carly Rae Jepsen" : "6sFIWsNpZYqfjUpaCgueju",
    "BTS" : "3kYFawNQVZ00FQbgs4rVBe",
    "Ace of Base" : "5ksRONqssB7BR161NTtJAm"
}


# -------------------- Functions --------------------

def sanitize_song_title(song_title):
    # Remove only specific unwanted patterns
    sanitized = re.sub(r'\s*\(Remix\)', '', song_title, flags=re.IGNORECASE)
    sanitized = re.sub(r'\s*\(Live\)', '', sanitized, flags=re.IGNORECASE)
    sanitized = sanitized.strip()
    logging.debug(f"Sanitized song title from '{song_title}' to '{sanitized}'.")
    return sanitized

def is_song_matching(song, expected_title, expected_artist, threshold=0.8):
    def similar(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    title_match = similar(song.title, expected_title) >= threshold
    artist_match = similar(song.artist, expected_artist) >= threshold
    return title_match and artist_match

def fetch_songwriter_from_genius(song_url):
    try:
        response = requests.get(song_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Updated selectors based on Genius's current HTML structure
        songwriters_section = soup.find('section', {'class': 'SongCredits'})
        if not songwriters_section:
            logging.warning(f"No songwriters section found on Genius page: {song_url}")
            return []

        songwriters = []
        for credit in songwriters_section.find_all('a', class_='SongCredit__AArtistLink'):
            songwriter = credit.get_text(strip=True)
            if songwriter:
                songwriters.append(songwriter)

        if not songwriters:
            logging.warning(f"No songwriters found on Genius page: {song_url}")

        return songwriters
    except requests.exceptions.Timeout:
        logging.error(f"Timeout while fetching Genius page: {song_url}")
        return []
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error while fetching Genius page {song_url}: {e}")
        return []
    except Exception as e:
        logging.error(f"Error fetching songwriter from Genius page {song_url}: {e}")
        return []

def fetch_lyrics_and_songwriters(artist_name, song_title, genius_client, retries=3):
    sanitized_title = sanitize_song_title(song_title)
    search_queries = [
        sanitized_title,
        song_title  # Try the original title if sanitized search fails
    ]

    for attempt in range(1, retries + 2):
        for query in search_queries:
            try:
                logging.debug(f"Searching for '{artist_name} - {query}' on Genius.")
                song = genius_client.search_song(title=query, artist=artist_name)
                if song and is_song_matching(song, song_title, artist_name):
                    if '/lyrics/' not in song.url:
                        logging.warning(f"Non-song URL returned: {song.url}")
                        continue  # Skip non-song URLs

                    logging.info(f"Successfully found lyrics for '{artist_name} - {song.title}' at {song.url}.")
                    cleaned_lyrics = clean_lyrics(song.lyrics, song_title)
                    songwriters = fetch_songwriter_from_genius(song.url) or [artist_name]
                    return cleaned_lyrics, songwriters
                else:
                    if song:
                        logging.warning(f"Search result mismatch for '{artist_name} - {song_title}' with query '{query}'. Found '{song.title}' by '{song.artist}'.")
                    else:
                        logging.warning(f"No song found for '{artist_name} - {song_title}' with query '{query}'.")
            except Exception as e:
                logging.error(f"Error during search for '{artist_name} - {song_title}' with query '{query}': {e}")
                continue  # Proceed to next query or retry

        logging.warning(f"Attempt {attempt} failed for '{artist_name} - {song_title}'. Retrying after delay...")
        time.sleep(5)  # Wait before retrying

    logging.error(f"Failed to fetch lyrics for '{artist_name} - {song_title}' after {retries} retries.")
    return None, []


def get_artist_top_tracks_by_id(artist_id, sp_client, top_n=10):
    """
    Fetches the top N tracks for a given artist using their Spotify artist ID.

    Parameters:
    - artist_id (str): Spotify artist ID.
    - sp_client (spotipy.Spotify): Authenticated Spotify client.
    - top_n (int): Number of top tracks to fetch.

    Returns:
    - list of dict: List containing track information dictionaries.
    """
    tracks = []
    fetched_track_ids = set()

    for attempt in range(1, SPOTIFY_MAX_RETRIES + 1):
        try:
            # 1. Get top tracks (max 10)
            top_tracks = sp_client.artist_top_tracks(artist_id, country='US').get('tracks', [])
            for track in top_tracks:
                track_id = track.get('id')
                if track_id and track_id not in fetched_track_ids:
                    tracks.append(track)
                    fetched_track_ids.add(track_id)

            logging.info(f"Fetched {len(top_tracks)} top tracks for artist ID {artist_id}.")

            # 2. If needed, fetch more from albums/singles
            if len(tracks) < top_n:
                albums = sp_client.artist_albums(artist_id, album_type='album,single', limit=50)
                album_ids = [album['id'] for album in albums.get('items', [])]
                logging.info(f"Fetched {len(album_ids)} albums/singles for artist ID {artist_id}.")

                for album_id in album_ids:
                    album_tracks = sp_client.album_tracks(album_id)
                    for track in album_tracks.get('items', []):
                        if len(tracks) >= top_n:
                            break
                        track_id = track.get('id')
                        if track_id and track_id not in fetched_track_ids:
                            tracks.append(track)
                            fetched_track_ids.add(track_id)
                    if len(tracks) >= top_n:
                        break
                logging.info(f"Total tracks after fetching from albums: {len(tracks)}.")

            # 3. Slice to top_n
            tracks = tracks[:top_n]
            logging.info(f"Final number of tracks for artist ID {artist_id}: {len(tracks)}.")

            # 4. Extract track information
            track_info = []
            for track in tracks:
                album_info = track.get('album')
                if not album_info:
                    logging.warning(f"Missing 'album' in track: {track.get('name', 'Unknown Track')}")
                    continue  # Skip tracks without album info

                album_name = album_info.get('name', 'Unknown Album')
                release_date = album_info.get('release_date', 'Unknown Release Date')
                track_name = track.get('name', 'Unknown Track')
                duration_ms = track.get('duration_ms', 0)
                song_length = f"{int(duration_ms / 60000)}:{int((duration_ms % 60000)/1000):02d}"
                popularity = track.get('popularity', 0)
                songwriters = [artist['name'] for artist in track.get('artists', [])]

                track_data = {
                    'track_name': track_name,
                    'album': album_name,
                    'release_date': release_date,
                    'song_length': song_length,
                    'popularity': popularity,
                    'songwriters': songwriters  # Placeholder; will replace with precise data
                }
                track_info.append(track_data)

            logging.info(f"Extracted information for {len(track_info)} tracks.")
            return track_info

        except (ReadTimeout, ConnectionError) as e:
            logging.warning(f"Network error on attempt {attempt} for artist ID {artist_id}: {e}. Retrying after {SPOTIFY_BACKOFF_FACTOR ** attempt} seconds...")
            time.sleep(SPOTIFY_BACKOFF_FACTOR ** attempt)
            continue
        except HTTPError as e:
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 5))
                logging.warning(f"Rate limit hit for artist ID {artist_id}. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            else:
                logging.error(f"HTTP error on attempt {attempt} for artist ID {artist_id}: {e}.")
                break
        except Exception as e:
            logging.error(f"Unexpected error on attempt {attempt} for artist ID {artist_id}: {e}.")
            break

    logging.error(f"Failed to fetch top tracks for artist ID {artist_id} after {SPOTIFY_MAX_RETRIES} attempts.")
    return []

def clean_lyrics(lyrics, song_title):
    """
    Cleans the lyrics by removing unwanted translation prefixes and other unwanted text,
    while retaining session headers like [Chorus], [Verse 1], etc.

    Parameters:
    - lyrics (str): The raw lyrics fetched from Genius.
    - song_title (str): The title of the song, used to accurately remove unwanted prefixes.

    Returns:
    - str: The cleaned lyrics, or the original lyrics if cleaning fails.
    """
    # Remove any unwanted translation prefixes before the lyrics
    # Assume that the actual lyrics start with a session header like [Intro], [Verse 1], etc.
    start_idx = lyrics.find('[')
    if start_idx != -1:
        lyrics = lyrics[start_idx:]
    else:
        # Log a warning if no session headers are found
        logging.warning(f"Lyrics for song '{song_title}' do not contain session headers.")
        # Proceed to save lyrics as-is
        return lyrics.strip()

    # Split lyrics into lines
    lines = lyrics.split('\n')

    # Define unwanted language substrings
    unwanted_languages = ['Trke', 'Español', 'Português', 'Italiano', 'Deutsch', 'Српски', 
                          'Franais', 'Türkçe', 'Ελληνικά', 'Français', 'فارسی', 'العربية']

    # Define unwanted promotional patterns
    unwanted_promotions = [r'See .* LiveGet tickets as low as', r'You might also like']

    cleaned_lines = []
    for line in lines:
        # Skip lines that start with 'Translations' or contain unwanted language substrings
        if line.startswith('Translations') or any(lang in line for lang in unwanted_languages):
            continue
        # Skip lines that match unwanted promotional patterns
        if any(re.search(pattern, line) for pattern in unwanted_promotions):
            continue
        # Remove 'numberEmbed' or 'number Contributors' within lines
        line = re.sub(r'\d+Embed', '', line)
        line = re.sub(r'\d+ Contributors', '', line)
        cleaned_lines.append(line)

    # Join the cleaned lines back into a single string
    cleaned_lyrics = '\n'.join(cleaned_lines).strip()

    # Additional validation:
    # Check if lyrics start with '['
    if not cleaned_lyrics.startswith('['):
        logging.warning(f"Lyrics for song '{song_title}' do not start with '[' after cleaning.")
        # Proceed to save lyrics as-is
        return lyrics.strip()

    # Check for unwanted content like lists of songs
    unwanted_patterns = [r'^Top canciones de', r'^New Music Friday']
    if any(re.match(pattern, cleaned_lyrics, flags=re.IGNORECASE) for pattern in unwanted_patterns):
        logging.warning(f"Lyrics for song '{song_title}' contain unwanted content.")
        # Proceed to save lyrics as-is
        return lyrics.strip()

    # Optional: Check for minimum length to ensure lyrics are substantial
    if len(cleaned_lyrics) < 100:
        logging.warning(f"Lyrics for song '{song_title}' are too short after cleaning.")
        # Proceed to save lyrics as-is
        return lyrics.strip()

    return cleaned_lyrics

def get_artist_genres(artist_name, sp_client):
    """
    Retrieves genres associated with an artist from Spotify.

    Parameters:
    - artist_name (str): Name of the artist.
    - sp_client (spotipy.Spotify): Authenticated Spotify client.

    Returns:
    - list of str: List containing genres associated with the artist.
    """
    try:
        results = sp_client.search(q='artist:' + artist_name, type='artist', limit=1)
        items = results['artists']['items']
        if not items:
            logging.warning(f"No artist found for genres: {artist_name}")
            return []
        artist = items[0]
        genres = artist.get('genres', [])
        logging.info(f"Fetched genres for artist '{artist_name}': {genres}")
        return genres
    except Exception as e:
        logging.error(f"Error fetching genres for artist '{artist_name}': {e}")
        return []

def upload_to_huggingface(json_file, readme_content, repo_id, hf_token):
    """
    Uploads the dataset and README to Hugging Face.

    Parameters:
    - json_file (str): Path to the JSON dataset file.
    - readme_content (str): Content for README.md.
    - repo_id (str): Repository ID in the format 'username/repo_name'.
    - hf_token (str): Hugging Face API token.
    """
    try:
        # Create repository if it doesn't exist
        create_repo(name=repo_id, token=hf_token, exist_ok=True)
        logging.info(f"Created or verified existence of Hugging Face repository: {repo_id}")

        # Upload the JSON file
        upload_file(
            path_or_fileobj=json_file,
            path_in_repo=os.path.basename(json_file),
            repo_id=repo_id,
            token=hf_token
        )
        logging.info(f"Uploaded JSON dataset to Hugging Face repository: {repo_id}")

        # Upload README.md
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)

        upload_file(
            path_or_fileobj="README.md",
            path_in_repo="README.md",
            repo_id=repo_id,
            token=hf_token
        )
        logging.info(f"Uploaded README.md to Hugging Face repository: {repo_id}")

        print(f"Dataset uploaded to https://huggingface.co/{repo_id}")
    except Exception as e:
        logging.error(f"Failed to upload to Hugging Face: {e}")
        print(f"Failed to upload to Hugging Face: {e}")

# -------------------- Data Collection --------------------

def load_top_tracks(json_path=TOP_TRACKS_JSON):
    """
    Loads top tracks from a JSON file if it exists.

    Parameters:
    - json_path (str): Path to the JSON file containing top tracks.

    Returns:
    - list of dict: List of track information dictionaries.
    """
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                top_tracks = json.load(f)
            logging.info(f"Loaded top tracks from {json_path}.")
            return top_tracks
        except Exception as e:
            logging.error(f"Failed to load {json_path}: {e}")
            return []
    else:
        logging.info(f"{json_path} does not exist. Proceeding to fetch top tracks from Spotify.")
        return []

def save_top_tracks(tracks, json_path=TOP_TRACKS_JSON):
    """
    Saves top tracks to a JSON file.

    Parameters:
    - tracks (list of dict): List of track information dictionaries.
    - json_path (str): Path to the JSON file to save top tracks.
    """
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tracks, f, ensure_ascii=False, indent=4)
        logging.info(f"Saved top tracks to {json_path}.")
    except Exception as e:
        logging.error(f"Failed to save top tracks to {json_path}: {e}")

def fetch_all_top_tracks():
    """
    Fetches top tracks for all artists. If top_tracks.json exists, uses it.
    Otherwise, fetches from Spotify and saves to top_tracks.json.

    Returns:
    - list of dict: List containing track information dictionaries.
    """
    top_tracks = load_top_tracks()

    if top_tracks:
        # Assuming top_tracks.json contains tracks for all artists
        return top_tracks
    else:
        # Fetch top tracks from Spotify
        all_tracks = []
        for artist, artist_id in tqdm(artists_with_ids.items(), desc="Fetching top tracks"):
            tracks = get_artist_top_tracks_by_id(artist_id, sp, top_n=10)  # Fetch top 10 tracks
            logging.info(f"Processing {len(tracks)} tracks for artist '{artist}'.")
            for track in tracks:
                track['artist'] = artist  # Add artist name to the track
            all_tracks.extend(tracks)
            time.sleep(1)  # Respect rate limits

        # Save fetched tracks to top_tracks.json
        save_top_tracks(all_tracks)

        return all_tracks

# -------------------- Data Structuring --------------------

def save_dataset_incrementally(track, json_path=DATASET_JSON):
    """
    Appends a single track's data to the JSON file.

    Parameters:
    - track (dict): Track information dictionary.
    - json_path (str): Path to the JSON file to save the dataset.
    """
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r+', encoding='utf-8') as f:
                data = json.load(f)
                data.append(track)
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump([track], f, ensure_ascii=False, indent=4)
        logging.info(f"Appended track '{track['track_name']}' to {json_path}.")
    except Exception as e:
        logging.error(f"Failed to append track to {json_path}: {e}")

def structure_dataset(tracks):
    """
    Structures the dataset by fetching lyrics and songwriters, and adding genres.

    Parameters:
    - tracks (list of dict): List containing track information dictionaries.

    Returns:
    - list of dict: Structured dataset ready for saving.
    """
    structured_data = []
    for track in tqdm(tracks, desc="Processing tracks"):
        artist = track.get('artist')
        track_name = track.get('track_name')

        if not artist or not track_name:
            logging.warning(f"Missing artist or track name in track: {track}")
            continue

        lyrics, songwriters = fetch_lyrics_and_songwriters(artist, track_name, genius)

        genre = get_artist_genres(artist, sp)

        structured_track = {
            'track_name': track_name,
            'album': track.get('album', 'Unknown Album'),
            'release_date': track.get('release_date', 'Unknown Release Date'),
            'song_length': track.get('song_length', '0:00'),
            'popularity': track.get('popularity', 0),
            'songwriters': songwriters,
            'artist': artist,
            'lyrics': lyrics,
            'genre': genre
        }

        structured_data.append(structured_track)
        save_dataset_incrementally(structured_track)  # Save each track incrementally

    return structured_data

# -------------------- Saving the Dataset --------------------

def save_dataset_incrementally(track, json_path=DATASET_JSON):
    """
    Appends a single track's data to the JSON file.

    Parameters:
    - track (dict): Track information dictionary.
    - json_path (str): Path to the JSON file to save the dataset.
    """
    try:
        # Check if the file exists and is not empty
        if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
            with open(json_path, 'r+', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    logging.error(f"Corrupted JSON file: {json_path}. Reinitializing.")
                    data = []  # Reinitialize if corrupted

                data.append(track)
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            # Initialize the file with an empty list if it doesn't exist or is empty
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump([track], f, ensure_ascii=False, indent=4)
        logging.info(f"Appended track '{track['track_name']}' to {json_path}.")
    except Exception as e:
        logging.error(f"Failed to append track to {json_path}: {e}")
# -------------------- Uploading to Hugging Face --------------------

def upload_dataset_to_huggingface(json_file, readme_content, repo_id, hf_token):
    """
    Uploads the dataset and README to Hugging Face.

    Parameters:
    - json_file (str): Path to the JSON dataset file.
    - readme_content (str): Content for README.md.
    - repo_id (str): Repository ID in the format 'username/repo_name'.
    - hf_token (str): Hugging Face API token.
    """
    try:
        # Create repository if it doesn't exist
        create_repo(name=repo_id, token=hf_token, exist_ok=True)
        logging.info(f"Created or verified existence of Hugging Face repository: {repo_id}")

        # Upload the JSON file
        upload_file(
            path_or_fileobj=json_file,
            path_in_repo=os.path.basename(json_file),
            repo_id=repo_id,
            token=hf_token
        )
        logging.info(f"Uploaded JSON dataset to Hugging Face repository: {repo_id}")

        # Upload README.md
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)

        upload_file(
            path_or_fileobj="README.md",
            path_in_repo="README.md",
            repo_id=repo_id,
            token=hf_token
        )
        logging.info(f"Uploaded README.md to Hugging Face repository: {repo_id}")

        print(f"Dataset uploaded to https://huggingface.co/{repo_id}")
    except Exception as e:
        logging.error(f"Failed to upload to Hugging Face: {e}")
        print(f"Failed to upload to Hugging Face: {e}")

# -------------------- Main Execution --------------------

def main():
    # Step 1: Fetch or Load Top Tracks
    top_tracks = fetch_all_top_tracks()

    if not top_tracks:
        logging.error("No tracks available to process. Exiting.")
        print("No tracks available to process. Please check the logs for details.")
        return

    # Step 2: Structure the Dataset
    structured_dataset = structure_dataset(top_tracks)

    # Step 3: Save the Dataset
    save_dataset_incrementally(structured_dataset)

    # Step 4: Upload to Hugging Face (Optional)
    # Define README content
    readme_content = """
# Pop Lyrics Dataset (Up to 1,000 Songs)

## Dataset Summary
This dataset contains up to 1,000 pop lyrics from various artists along with associated metadata, including artist names, album details, release dates, and genres. The dataset is intended for language model training, sentiment analysis, and creative applications such as automatic lyric generation.

## Dataset Structure

Each entry in the dataset contains the following fields:
- `track_name`: Name of the track.
- `album`: The album in which the song was released.
- `release_date`: The song's release date.
- `song_length`: Length of the song in minutes and seconds.
- `popularity`: Spotify's popularity metric for the track.
- `songwriters`: List of songwriters.
- `artist`: Name of the artist.
- `lyrics`: The full lyrics of the song.
- `genre`: List of genres associated with the artist.

## License
This dataset is intended for educational and research purposes. Please respect copyright laws when using the lyrics.
"""

    # Uncomment the following lines to upload to Hugging Face
    # repo_id = f"{HUGGINGFACE_USERNAME}/{REPO_NAME}"
    # upload_dataset_to_huggingface(
    #     json_file=DATASET_JSON,
    #     readme_content=readme_content,
    #     repo_id=repo_id,
    #     hf_token=HF_TOKEN
    # )

if __name__ == "__main__":
    main()