import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import time
from tqdm import tqdm
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
names_logger = logging.getLogger('names')
spotify_logger = logging.getLogger('spotify')

# File handlers for different logs
names_handler = logging.FileHandler('names.log')
spotify_handler = logging.FileHandler('spotify.log')

# Set level and format for handlers
names_handler.setLevel(logging.INFO)
spotify_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
names_handler.setFormatter(formatter)
spotify_handler.setFormatter(formatter)

# Add handlers to loggers
names_logger.addHandler(names_handler)
spotify_logger.addHandler(spotify_handler)

# Spotify API credentials from environment variables
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', 'your_spotify_client_id')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', 'your_spotify_client_secret')

# Authenticate with Spotify
client_credentials_manager = SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

"""
#Done
    "Lady Gaga",
    "Hayd",
    "Justin Bieber",
    "The Kid LAROI",
    "Ed Sheeran",
    "Charlie Puth",
    "Shawn Mendes",
    "JVKE",
    "Lauv",
    "Stephen Sanchez",
    "Benson Boone",
    "Harry Styles",
    "Conan Gray",
    "Chappell Roan",
    "Halsey",
    "Sabrina Carpenter",
    "Taylor Swift",
    "Ariana Grande",
    "Sasha Alex Sloan",
    "Ali Gatie",
    "Bruno Mars",
    "Dua Lipa",
    "Billie Eilish",
    "Katy Perry",
    "David Kushner",
    "Myles Smith",
    "FINNEAS",
    "Post Malone",
    "SZA",
    "Hozier",
    "The Weeknd",
    "Coldplay",
    "Tate McRae",
    "Frank Ocean",
    "Alec Benjamin",
    "Cigarettes After Sex",
    "Gracie Abrams",
    "Olivia Rodrigo",
    "Michael Jackson",
    "Future",
    "Miley Cyrus",
    "Doja Cat",
    "Karol G",
    "Jimin",
    "Lana Del Rey",
    "Melanie Martinez",
    #
    "Jennifer Lopez",
    "Beyoncé",
    "Madonna",
    "Britney Spears",
    "Justin Timberlake",
    "Elton John",
    "Celine Dion",
    "Prince",
    "The Beach Boys",
    "Selena Gomez",
    "Janet Jackson",
    "Adele",
    "Backstreet Boys",
    "Christina Aguilera",
    "Usher",
    "The Jackson 5",
    "Pink",
    "Kelly Clarkson",
    "Jonas Brothers",
    "The Black Eyed Peas",
    "Spice Girls",
    "Cher",
    "Shakira",
    "Gwen Stefani",
    "'N Sync",
    "Cyndi Lauper",
    "Paula Abdul",
    "New Kids on the Block",
    "Demi Lovato",
    "R. Kelly",
    "Nick Jonas",
    "Maroon 5",
    "Chris Brown",
    "Barry Manilow",
    "One Direction",
    "Sinéad O'Connor",

"""
# List of artists
artists = [    
    "Michael Bublé", #Last Run
    "Susan Boyle",
    "Smash Mouth",
    "Steely Dan",
    "Ashlee Simpson",
    "WHAM!",
    "Victoria Beckham",
    "The Bangles",
    "Johnny Mathis",
    "Joni Mitchell",
    "Harry Connick, Jr.",
    "OneRepublic",
    "Sam Smith",
    "Engelbert Humperdinck",
    "Rick Astley",
    "Anne Murray",
    "Sia",
    "Fiona Apple",
    "Kylie Minogue",
    "Carly Rae Jepsen",
    "BTS", 
    "Ace of Base", 
]


print(len(set(artists)))  # Should print the number of unique artists

def get_artist_song_count(artist_name, sp_client, max_retries=3):
    """
    Fetches the number of songs by an artist from Spotify with retry logic.

    Parameters:
    - artist_name (str): Name of the artist.
    - sp_client (spotipy.Spotify): Authenticated Spotify client.
    - max_retries (int): Maximum number of retries for failed requests.

    Returns:
    - int: Number of songs by the artist.
    - str: Spotify URL for the artist.
    """
    print(f"Processing artist: {artist_name}")
    retries = 0
    while retries < max_retries:
        try:
            # Search for the artist
            results = sp_client.search(q='artist:' + artist_name, type='artist', limit=1)
            items = results['artists']['items']

            if len(items) == 0:
                print(f"No artist found for {artist_name}")
                return 0, ""

            artist = items[0]
            artist_id = artist['id']
            artist_url = artist['external_urls']['spotify']

            song_count = 0
            limit = 50

            # Album types to fetch
            album_types = ['album', 'single', 'compilation']

            # Fetch songs from all album types
            for album_type in album_types:
                print(f"Fetching albums for {artist_name}, type: {album_type}")
                offset = 0  # Reset offset for each album type
                while True:
                    # Fetch the artist's albums
                    albums = sp_client.artist_albums(artist_id, album_type=album_type, limit=limit, offset=offset)

                    if len(albums['items']) == 0:
                        print(f"No more albums for {artist_name}, type: {album_type}")
                        break  # Exit if no more albums

                    for album in albums['items']:
                        album_id = album['id']
                        album_name = album['name']
                        print(f"Fetching tracks for album: {album_name} (ID: {album_id})")
                        tracks = sp_client.album_tracks(album_id)
                        song_count += len(tracks['items'])

                    offset += limit  # Move to the next page of albums
                    print(f"Processed {offset} albums for {artist_name}, type: {album_type}")
                    time.sleep(0.1)  # Small delay to prevent hitting rate limits

            print(f"{artist_name}: {song_count} songs - Spotify URL: {artist_url}\n")
            # Log the results
            names_logger.info(f'"{artist_name}" : "{artist_id}"')
            spotify_logger.info(f"{artist_name}: {song_count} songs - Spotify URL: {artist_url}")
            return song_count, artist_url

        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                retry_after = int(e.headers.get('Retry-After', 5))
                print(f"Rate limit exceeded. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                retries += 1
            else:
                print(f"SpotifyException for artist {artist_name}: {e}")
                return 0, ""
        except Exception as e:
            print(f"Error processing artist {artist_name}: {e}")
            return 0, ""

    print(f"Max retries exceeded for artist {artist_name}. Skipping...")
    return 0, ""

# Check the number of songs for each artist with a progress bar
artist_song_counts = {}
for artist in tqdm(artists, desc="Processing Artists"):
    count, url = get_artist_song_count(artist, sp)
    artist_song_counts[artist] = count
    print(f"{artist}: {count} songs - Spotify URL: {url}")

# Check if all artists have at least 22 songs
all_have_at_least_22 = all(count >= 22 for count in artist_song_counts.values())
print(f"Do all artists have at least 22 songs? {'Yes' if all_have_at_least_22 else 'No'}")