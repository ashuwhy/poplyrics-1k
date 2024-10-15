import os

def load_tracks(file_path, remove_dash=False):
    """
    Loads track names from a text file.

    Args:
        file_path (str): The path to the text file containing track names.
        remove_dash (bool): If True, removes leading dashes and spaces from each line.

    Returns:
        set: A set of cleaned track names.
    """
    tracks = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if remove_dash:
                    if line.startswith("- "):
                        line = line[2:]
                if line:  # Ensure the line is not empty
                    tracks.add(line.lower())  # Using lowercase for case-insensitive comparison
        return tracks
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return set()
    except Exception as e:
        print(f"An error occurred while reading {file_path}: {e}")
        return set()

def compare_tracks(defective_file, test_file):
    """
    Compares tracks from defective_tracks.txt and test.txt.

    Args:
        defective_file (str): Path to defective_tracks.txt.
        test_file (str): Path to test.txt.

    Returns:
        tuple: A tuple containing two sets:
            - Tracks present in both files.
            - Tracks in defective_tracks.txt but not in test.txt.
    """
    defective_tracks = load_tracks(defective_file)
    test_tracks = load_tracks(test_file, remove_dash=True)

    common_tracks = defective_tracks.intersection(test_tracks)
    unique_defective_tracks = defective_tracks.difference(test_tracks)

    return common_tracks, unique_defective_tracks

def main():
    # Define file paths
    defective_file = 'defective_tracks.txt'
    test_file = 'test.txt'

    # Check if files exist
    if not os.path.isfile(defective_file):
        print(f"Error: {defective_file} does not exist.")
        return
    if not os.path.isfile(test_file):
        print(f"Error: {test_file} does not exist.")
        return

    # Compare tracks
    common, unique_defective = compare_tracks(defective_file, test_file)

    # Display Results
    print("\n## Tracks Present in Both Files:")
    if common:
        for track in sorted(common):
            print(f"- {track.title()}")
    else:
        print("No common tracks found.")

    print("\n## Tracks in `defective_tracks.txt` but Not in `test.txt`:")
    if unique_defective:
        for track in sorted(unique_defective):
            print(f"- {track.title()}")
    else:
        print("All tracks in `defective_tracks.txt` are also in `test.txt`.")

if __name__ == "__main__":
    main()
