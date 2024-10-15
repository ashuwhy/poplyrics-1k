import json

def print_json_error_context(file_path, error_position, context_lines=5):
    with open(file_path, 'r') as file:
        lines = file.readlines()
     
    error_line = error_position[0]
    start_line = max(0, error_line - context_lines - 1)
    end_line = min(len(lines), error_line + context_lines)
    
    print(f"Error near line {error_line}:")
    for i, line in enumerate(lines[start_line:end_line], start=start_line + 1):
        print(f"{i}: {line.rstrip()}")
        if i == error_line:
            print(" " * (len(str(i)) + 2 + error_position[1]) + "^")

try:
    # Load the JSON data
    with open('pop_lyrics_dataset.json', 'r') as file:
        data = json.load(file)

    # Iterate through the data and print track names with null lyrics
    for track in data:
        if track['lyrics'] is None:
            print(track['track_name'])

except json.JSONDecodeError as e:
    print(f"JSON Decode Error: {e}")
    print_json_error_context('pop_lyrics_dataset.json', (e.lineno, e.colno))
    print("\nPlease check your JSON file for formatting errors.")

except FileNotFoundError:
    print("Error: The file 'pop_lyrics_dataset.json' was not found.")

except Exception as e:
    print(f"An unexpected error occurred: {e}")
