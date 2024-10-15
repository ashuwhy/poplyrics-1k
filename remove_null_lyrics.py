def remove_null_lyrics(input_file, output_file):
    """
    Removes tracks with null lyrics from the JSON dataset.

    Args:
        input_file (str): Path to the input JSON file containing track data.
        output_file (str): Path to save the filtered JSON data.
    """
    import json

    # Load the JSON data from the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

    # Check if the data is a list
    if not isinstance(data, list):
        print("JSON data is not a list of tracks.")
        return

    # Filter out tracks where 'lyrics' is null or None
    filtered_data = [track for track in data if track.get('lyrics') is not None]

    # Save the filtered data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_data, f, ensure_ascii=False, indent=4)

    print(f"Filtered data saved to {output_file}")

def main():
    input_path = 'pop_lyrics_dataset.json'
    output_path = 'filtered_pop_lyrics_dataset.json'
    remove_null_lyrics(input_path, output_path)

if __name__ == "__main__":
    main()
