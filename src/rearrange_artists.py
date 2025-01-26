import json
from collections import defaultdict

class SongOrganizer:
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
    
    def organize_songs_by_artist(self):
        """
        Reads JSON data from input_file, groups songs by artist,
        and writes the organized data to output_file.
        """
        try:
            # Load the data from the JSON file
            with open(self.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Error: The file {self.input_file} does not exist.")
            return
        except json.JSONDecodeError:
            print(f"Error: The file {self.input_file} is not a valid JSON file.")
            return
        
        # Group songs by artist
        artist_dict = defaultdict(list)
        for song in data:
            artist = song.get('artist', 'Unknown Artist')
            artist_dict[artist].append(song)
        
        # Convert defaultdict to regular dict for JSON serialization
        organized_data = dict(artist_dict)
        
        try:
            # Save the grouped data to the output file
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(organized_data, f, indent=4)
            print(f"Songs have been organized by artist and saved to '{self.output_file}'.")
        except IOError:
            print(f"Error: Could not write to file {self.output_file}.")

if __name__ == "__main__":
    input_file = 'filtered_pop_lyrics_dataset.json'
    output_file = 'songs_by_artist.json'
    organizer = SongOrganizer(input_file, output_file)
    organizer.organize_songs_by_artist()