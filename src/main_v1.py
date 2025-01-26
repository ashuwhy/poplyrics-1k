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

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename='dataset_builder.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Environment variables and constants
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'your_spotify_client_id')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'your_spotify_client_secret')
GENIUS_API_TOKEN = os.getenv('GENIUS_API_TOKEN', 'your_genius_api_token')
HUGGINGFACE_USERNAME = os.getenv('HUGGINGFACE_USERNAME', 'your_username')
REPO_NAME = os.getenv('REPO_NAME', 'pop-lyrics-dataset')
HF_TOKEN = os.getenv('HF_TOKEN', 'your_hf_token')

SPOTIFY_MAX_RETRIES = 3
SPOTIFY_BACKOFF_FACTOR = 2

TOP_TRACKS_JSON = 'top_tracks.json'
DATASET_JSON = 'pop_lyrics_dataset.json'

# Initialize requests session
session = requests.Session()

# Initialize Spotify client
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
)

# Initialize Genius client
genius = Genius(
    GENIUS_API_TOKEN,
    timeout=15,
    retries=3,
    remove_section_headers=False,  
    skip_non_songs=False,
    excluded_terms=["(Remix)", "(Live)"]
)

# Dictionary of artists with their Spotify IDs
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

def sanitize_song_title(song_title):
    """
    Remove parenthetical statements and extra whitespace from song titles.
    """
    sanitized = re.sub(r'\s*\(.*?\)', '', song_title).strip()
    logging.debug(f"Sanitized song title from '{song_title}' to '{sanitized}'.")
    return sanitized

def parse_artists(fetched_artists):
    """
    Parse the fetched artist string into a list of individual artist names.
    """
    # Split by '&', ',', 'feat.', 'ft.', etc.
    artists = re.split(r'\s*&\s*|\s*,\s*|\s*feat\.?\s*|\s*ft\.?\s*', fetched_artists.lower())
    # Strip whitespace and capitalize each artist's name
    artists = [artist.strip().title() for artist in artists]
    logging.debug(f"Parsed artists from '{fetched_artists}' to {artists}.")
    return artists

def get_artist_top_tracks_by_id(artist_id, sp_client, top_n=10):
    """
    Fetch the top tracks for a given artist from Spotify.
    """
    tracks = []
    fetched_track_ids = set()

    for attempt in range(1, SPOTIFY_MAX_RETRIES + 1):
        try:
            top_tracks = sp_client.artist_top_tracks(artist_id, country='US').get('tracks', [])
            for track in top_tracks:
                track_id = track.get('id')
                if track_id and track_id not in fetched_track_ids:
                    tracks.append(track)
                    fetched_track_ids.add(track_id)

            logging.info(f"Fetched {len(top_tracks)} top tracks for artist ID {artist_id}.")

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

            tracks = tracks[:top_n]
            logging.info(f"Final number of tracks for artist ID {artist_id}: {len(tracks)}.")

            track_info = []
            for track in tracks:
                album_info = track.get('album')
                if not album_info:
                    logging.warning(f"Missing 'album' in track: {track.get('name', 'Unknown Track')}")
                    continue 

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
                    'songwriters': songwriters 
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
    Clean the fetched lyrics by removing unwanted sections and characters.
    """
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

def fetch_songwriter_from_genius(song_url):
    """
    Extract songwriters from the Genius song page.
    """
    try:
        response = requests.get(song_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Possible class names where songwriters might be listed
        possible_classes = [
            'ContributorsCreditMetadataItem__Artists-sc-1cw8ns8-2',  # Existing class
            'SongInfo__InfoBlock-sc-1w2wxu2-3',  # Alternative class
            'SongInfo__Contributors-sc-1w2wxu2-4',  # Another alternative
        ]

        songwriters_section = None
        for class_name in possible_classes:
            songwriters_section = soup.find('div', class_=class_name)
            if songwriters_section:
                break

        if not songwriters_section:
            # Fallback: Look for "Writing Credits" section
            writing_credits = soup.find('h3', string=re.compile(r'Writing Credits', re.I))
            if writing_credits:
                parent = writing_credits.find_next_sibling('ul')
                if parent:
                    songwriters = [li.get_text(strip=True) for li in parent.find_all('li')]
                    if songwriters:
                        return songwriters
            logging.warning(f"No songwriters found on Genius page: {song_url}")
            return []

        # Extract songwriters from the found section
        songwriters = [a.get_text(strip=True) for a in songwriters_section.find_all('a', class_=re.compile(r'StyledLink'))]

        if not songwriters:
            # Fallback: Extract from list items
            songwriters = [li.get_text(strip=True) for li in songwriters_section.find_all('li')]
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
    """
    Fetch lyrics and songwriters for a given song using Genius.
    """
    song = None 
    sanitized_title = sanitize_song_title(song_title)

    for attempt in range(1, retries + 2):  
        try:
            if song is None:
                song = genius_client.search_song(title=sanitized_title, artist=artist_name)
            if song is None:
                logging.warning(f"[Attempt {attempt}] Lyrics not found for '{artist_name}' - '{sanitized_title}'.")
                return None, [artist_name]  # Default to artist name if lyrics not found

            # Verify that the fetched song matches the artist and title
            fetched_artists = parse_artists(song.artist)
            expected_artist = artist_name.lower().strip()
            if expected_artist not in [artist.lower() for artist in fetched_artists]:
                logging.warning(f"[Attempt {attempt}] Expected artist '{artist_name}' not found in fetched song artists {fetched_artists}. URL: {song.url}")
                return None, [artist_name]  # Default to artist name if mismatch

            # Additional validation: Ensure the URL does not contain unwanted substrings
            unwanted_substrings = ['annotated', 'user', 'discography']
            if any(sub in song.url.lower() for sub in unwanted_substrings):
                logging.warning(f"[Attempt {attempt}] Fetched URL contains unwanted substrings for '{artist_name}' - '{sanitized_title}'. URL: {song.url}")
                return None, [artist_name]  # Default to artist name if URL is incorrect

            cleaned_lyrics = clean_lyrics(song.lyrics, song_title)

            songwriters = fetch_songwriter_from_genius(song.url)
            if not songwriters:
                # Default to artist name if songwriters not found
                songwriters = [artist_name]

            logging.info(f"Successfully fetched lyrics and songwriters for '{artist_name}' - '{song_title}'.")
            return cleaned_lyrics, songwriters

        except AttributeError as e:
            logging.warning(f"[Attempt {attempt}] Attribute error for song '{song_title}': {e}. Assuming no featured artists.")
            if song and hasattr(song, 'lyrics') and hasattr(song, 'url'):
                cleaned_lyrics = clean_lyrics(song.lyrics, song_title)
                songwriters = fetch_songwriter_from_genius(song.url) or [artist_name]
                return cleaned_lyrics, songwriters
            else:
                logging.error(f"[Attempt {attempt}] Missing attributes for song '{song_title}'.")
                return None, [artist_name]
        
        except requests.exceptions.Timeout:
            logging.warning(f"[Attempt {attempt}] Timeout while fetching lyrics for '{artist_name}' - '{song_title}'. Retrying...")
            time.sleep(5)  
            song = None  
            continue
        except Exception as e:
            logging.error(f"[Attempt {attempt}] Error fetching lyrics for '{artist_name}' - '{song_title}': {e}")
            time.sleep(5)  
            song = None 
            continue

    logging.error(f"Failed to fetch lyrics for '{artist_name}' - '{song_title}' after {retries} retries.")
    return None, [artist_name]

def get_artist_genres(artist_name, sp_client):
    """
    Fetch genres associated with an artist from Spotify.
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
    Upload the dataset and README to Hugging Face Hub.
    """
    try:
        create_repo(name=repo_id, token=hf_token, exist_ok=True)
        logging.info(f"Created or verified existence of Hugging Face repository: {repo_id}")

        upload_file(
            path_or_fileobj=json_file,
            path_in_repo=os.path.basename(json_file),
            repo_id=repo_id,
            token=hf_token
        )
        logging.info(f"Uploaded JSON dataset to Hugging Face repository: {repo_id}")

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

def load_top_tracks(json_path=TOP_TRACKS_JSON):
    """
    Load top tracks from a JSON file if it exists.
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
    Save top tracks to a JSON file.
    """
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(tracks, f, ensure_ascii=False, indent=4)
        logging.info(f"Saved top tracks to {json_path}.")
    except Exception as e:
        logging.error(f"Failed to save top tracks to {json_path}: {e}")

def fetch_all_top_tracks():
    """
    Fetch all top tracks for the specified artists.
    """
    top_tracks = load_top_tracks()

    if top_tracks:
        return top_tracks
    else:
        all_tracks = []
        for artist, artist_id in tqdm(artists_with_ids.items(), desc="Fetching top tracks"):
            tracks = get_artist_top_tracks_by_id(artist_id, sp, top_n=10) 
            logging.info(f"Processing {len(tracks)} tracks for artist '{artist}'.")
            for track in tracks:
                track['artist'] = artist 
            all_tracks.extend(tracks)
            time.sleep(1)  # Respectful delay between API calls

        save_top_tracks(all_tracks)

        return all_tracks

def save_dataset_incrementally(track, json_path=DATASET_JSON):
    """
    Append a single track to the dataset JSON file.
    """
    try:
        if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
            with open(json_path, 'r+', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    logging.error(f"Corrupted JSON file: {json_path}. Reinitializing.")
                    data = []  

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
    Process each track to fetch lyrics, songwriters, and genres, then structure the data.
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
        save_dataset_incrementally(structured_track) 

    return structured_data

def upload_dataset_to_huggingface(json_file, readme_content, repo_id, hf_token):
    """
    Wrapper function to upload dataset and README to Hugging Face.
    """
    try:
        create_repo(name=repo_id, token=hf_token, exist_ok=True)
        logging.info(f"Created or verified existence of Hugging Face repository: {repo_id}")

        upload_file(
            path_or_fileobj=json_file,
            path_in_repo=os.path.basename(json_file),
            repo_id=repo_id,
            token=hf_token
        )
        logging.info(f"Uploaded JSON dataset to Hugging Face repository: {repo_id}")

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

def main():
    """
    Main function to orchestrate the dataset building process.
    """
    top_tracks = fetch_all_top_tracks()

    if not top_tracks:
        logging.error("No tracks available to process. Exiting.")
        print("No tracks available to process. Please check the logs for details.")
        return

    structured_dataset = structure_dataset(top_tracks)

    # Separate successful and failed tracks
    successful_tracks = [track for track in structured_dataset if track.get('lyrics') and track.get('songwriters')]
    failed_tracks = [track for track in structured_dataset if not track.get('lyrics') or not track.get('songwriters')]

    if failed_tracks:
        logging.warning(f"{len(failed_tracks)} tracks failed to process. Consider reviewing them manually.")

    readme_content = """
# Pop Lyrics Dataset (Up to 1,000 Songs)

This dataset contains up to 1,000 pop songs with their lyrics, songwriters, genres, and other relevant metadata. The data was collected from Spotify and Genius.

## Dataset Structure

- **track_name**: Name of the song.
- **album**: Album name.
- **release_date**: Release date of the song.
- **song_length**: Duration of the song.
- **popularity**: Popularity score from Spotify.
- **songwriters**: List of songwriters.
- **artist**: Name of the artist.
- **lyrics**: Cleaned lyrics of the song.
- **genre**: List of genres associated with the artist.

## Usage

You can use this dataset for various NLP tasks such as sentiment analysis, lyric generation, or genre classification.

## Acknowledgements

- [Spotify](https://www.spotify.com) for providing track information.
- [Genius](https://genius.com) for providing song lyrics.
- [Hugging Face](https://huggingface.co) for hosting the dataset.

## License

This dataset is licensed under the [MIT License](LICENSE).
    """

    #upload_dataset_to_huggingface(DATASET_JSON, readme_content, REPO_NAME, HF_TOKEN)

if __name__ == "__main__":
    main()

