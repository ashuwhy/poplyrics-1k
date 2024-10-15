import requests
import json

# Replace with your actual Musixmatch API key
API_KEY = 'YOUR_MUSIXMATCH_API_KEY'
BASE_URL = 'https://api.musixmatch.com/ws/1.1/'

def search_track(track_title, artist_name=None, page=1, page_size=10):
    """
    Search for a track by title and optionally by artist name.
    """
    endpoint = f'{BASE_URL}track.search'
    params = {
        'apikey': API_KEY,
        'q_track': track_title,
        'q_artist': artist_name,
        'page': page,
        'page_size': page_size,
        's_track_rating': 'desc',
        'format': 'json'
    }
    response = requests.get(endpoint, params=params)
    
    # Debug: Print the status code and response text
    print(f"Response Status Code: {response.status_code}")
    print("Response JSON:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code != 200:
        print(f'Error: Received status code {response.status_code}')
        return None
    
    data = response.json()
    
    # Check if 'message' and 'body' are in the response
    if 'message' not in data or 'body' not in data['message']:
        print('Error: Unexpected response structure.')
        return None
    
    body = data['message']['body']
    
    # Check if 'track_list' exists and is a list
    if 'track_list' not in body or not isinstance(body['track_list'], list):
        print('Error: "track_list" not found in the response or is not a list.')
        return None
    
    track_list = body['track_list']
    
    if not track_list:
        print('No tracks found.')
        return None
    
    # Return the first track match
    return track_list[0]['track']

def get_track_details(track_id):
    """
    Get detailed information about a track by track ID.
    """
    endpoint = f'{BASE_URL}track.get'
    params = {
        'apikey': API_KEY,
        'track_id': track_id,
        'format': 'json'
    }
    response = requests.get(endpoint, params=params)
    
    # Debug: Print the status code and response text
    print(f"Response Status Code (Track Details): {response.status_code}")
    print("Track Details JSON:")
    print(json.dumps(response.json(), indent=2))
    
    if response.status_code != 200:
        print(f'Error: Received status code {response.status_code}')
        return None
    
    data = response.json()
    
    if 'message' not in data or 'body' not in data['message']:
        print('Error: Unexpected response structure.')
        return None
    
    body = data['message']['body']
    
    if 'track' not in body:
        print('Error: "track" not found in the response.')
        return None
    
    return body['track']

def main():
    # Example song details
    track_title = 'Shape of You'
    artist_name = 'Ed Sheeran'

    # Step 1: Search for the track
    track = search_track(track_title, artist_name)
    if not track:
        return

    track_id = track.get('track_id')
    track_name = track.get('track_name')
    artist = track.get('artist_name')

    if not track_id:
        print('Error: "track_id" not found.')
        return

    print(f'Found Track: "{track_name}" by {artist} (Track ID: {track_id})')

    # Step 2: Get track details
    details = get_track_details(track_id)
    if not details:
        return

    # Extract Genre Information
    primary_genres = details.get('primary_genres', {})
    genre_list = primary_genres.get('music_genre_list', [])
    if genre_list:
        genre = genre_list[0]['music_genre']['music_genre_name']
    else:
        genre = 'Genre information not available.'

    # Extract Songwriter Information
    # Note: Musixmatch API may not provide songwriter details directly.
    # This example assumes songwriter information is available under 'writer_list'
    # Modify according to the actual API response structure.
    songwriter_info = details.get('writer_list', [])
    if songwriter_info:
        songwriters = [writer['writer_name'] for writer in songwriter_info]
        songwriters = ', '.join(songwriters)
    else:
        songwriters = 'Songwriter information not available.'

    print(f'Genre: {genre}')
    print(f'Songwriters: {songwriters}')

if __name__ == '__main__':
    main()
