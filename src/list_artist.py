import json

# Load the JSON data from the file
with open('./songs_by_artist.json', 'r') as file:
    data = json.load(file)

# Iterate through the artists and their tracks
for artist, tracks in data.items():
    print(f"{artist}:")
    for track in tracks:
        print(f"  - {track['track_name']}")