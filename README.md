# Pop Lyrics Dataset

This dataset contains up to 1,000 pop songs with their lyrics, songwriters, genres, and other relevant metadata. The data was collected from Spotify and Genius.
Explore the dataset using the [interactive viewer](https://huggingface.co/datasets/ashuwhy/poplyrics-1k/embed/viewer/default/train).

## Hugging Face

- Dataset: [ashuwhy/poplyrics-1k](https://huggingface.co/datasets/ashuwhy/poplyrics-1k)
- Model: [ashuwhy/llama3.2-poplyrics-1k](https://huggingface.co/ashuwhy/llama3.2-poplyrics-1k)

## Dataset Structure

- **track_name**: Name of the song.
- **album**: Album name.
- **release_date**: Release date of the song.
- **song_length**: Duration of the song.
- **popularity**: Popularity score from Spotify.
- **songwriters**: List of songwriters.
- **artist**: Name of the artist.
- **lyrics**: Cleaned lyrics of the song.
- **genre**: List of genres associated with the artist.

## Usage

You can use this dataset for various NLP tasks such as sentiment analysis, lyric generation, or genre classification.

### Example Usage

```python
from datasets import load_dataset

dataset = load_dataset("ashuwhy/poplyrics-1k", split="train")
print(dataset)
```

## Acknowledgements

- [Spotify](https://www.spotify.com) for providing track information.
- [Genius](https://genius.com) for providing song lyrics.
- [Hugging Face](https://huggingface.co) for hosting the dataset.

## License

This dataset is licensed under the [MIT License](LICENSE).
