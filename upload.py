# -------------------- Uploading to Hugging Face --------------------

# Define README content
readme_content = """
# Pop Lyrics Dataset (1,000 Songs)

## Dataset Summary
This dataset contains 1,000 pop lyrics from various artists along with associated metadata, including artist names, album details, release dates, and genres. The dataset is intended for language model training, sentiment analysis, and creative applications such as automatic lyric generation.

## Dataset Structure

Each entry in the dataset contains the following fields:
- `track_name`: Name of the track.
- `album`: The album in which the song was released.
- `release_date`: The song's release date.
- `song_length`: Length of the song in minutes and seconds.
- `popularity`: Spotify's popularity metric for the track.
- `songwriters`: List of songwriters (approximated using artists).
- `artist`: Name of the artist.
- `lyrics`: The full lyrics of the song.
- `genre`: List of genres associated with the song (based on artist's genres).

## License
This dataset is intended for educational and research purposes. Please respect copyright laws when using the lyrics.
"""

# Upload to Hugging Face
upload_to_huggingface(
    json_file='pop_lyrics_dataset.json',
    readme_content=readme_content,
    repo_id=f"{HUGGINGFACE_USERNAME}/{REPO_NAME}",
    hf_token=HF_TOKEN
)
