import json

def extract_track_info(file_path):
    """
    Extracts all track names and their corresponding artists from the given JSON file.

    Args:
        file_path (str): The path to the JSON file containing track information.

    Returns:
        list of tuples: A list where each tuple contains (track_name, artist).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        track_info = [
            (track.get('track_name'), track.get('artist'))
            for track in data
            if 'track_name' in track and 'artist' in track
        ]
        return track_info
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the file: {file_path}")
        return []

def display_track_info(track_info):
    """
    Displays the extracted track names along with their artists.

    Args:
        track_info (list of tuples): The list containing track names and artists.
    """
    if track_info:
        print("Extracted Track Names and Artists:")
        for track_name, artist in track_info:
            print(f"- \"{track_name}\" by {artist}")
    else:
        print("No track information found or there was an error processing the file.")

if __name__ == "__main__":
    file_path = 'fixed_tracks.json'
    tracks = extract_track_info(file_path)
    display_track_info(tracks)