def extract_tracks_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    tracks = [line.strip() for line in lines if line.strip()]
    return tracks

def extract_processed_tracks_from_log(log_path):
    processed_tracks = []
    with open(log_path, 'r') as log_file:
        for line in log_file:
            if "Processing track:" in line:
                # Extract the track name from the log line
                track_name = line.split("Processing track:")[-1].strip()
                processed_tracks.append(track_name)
    return processed_tracks

def find_unprocessed_tracks(defective_tracks, processed_tracks):
    unprocessed_tracks = [track for track in defective_tracks if track not in processed_tracks]
    return unprocessed_tracks

# File paths
defective_tracks_file = 'defective_tracks.txt'
log_file = 'fix_tracks.log'

# Extract tracks
defective_tracks = extract_tracks_from_file(defective_tracks_file)
processed_tracks = extract_processed_tracks_from_log(log_file)

print(f"Total tracks in defective_tracks.txt: {len(defective_tracks)}")
print(f"Total processed tracks in fix_tracks.log: {len(processed_tracks)}")

# Find unprocessed tracks
unprocessed_tracks = find_unprocessed_tracks(defective_tracks, processed_tracks)

print("\nUnprocessed Tracks:")
for track in unprocessed_tracks:
    print(track)

print("\nAll tracks in defective_tracks.txt:")
for track in defective_tracks:
    print(track)

print("\nAll processed tracks in fix_tracks.log:")
for track in processed_tracks:
    print(track)
