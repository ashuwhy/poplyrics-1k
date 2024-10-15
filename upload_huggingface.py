import json
import logging
from huggingface_hub import create_repo, upload_file
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()   

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    filename='uploader_builder.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HUGGINGFACE_USERNAME = os.getenv('HUGGINGFACE_USERNAME')
REPO_NAME = os.getenv('REPO_NAME')  # Ensure this is set to "alexshcer/poplyric-1k"
HF_TOKEN = os.getenv('HF_TOKEN')
DATASET_JSON = 'filtered_pop_lyrics_dataset.json'

def upload_dataset_to_huggingface(json_file, readme_content, repo_id, hf_token):
    """
    Wrapper function to upload dataset and README to Hugging Face.
    """
    try:
        print("Creating or verifying repository...")
        # Update the create_repo call to use the correct parameters
        create_repo(repo_id, token=hf_token, exist_ok=True)
        logging.info(f"Created or verified existence of Hugging Face repository: {repo_id}")

        print("Uploading JSON dataset...")
        upload_file(
            path_or_fileobj=json_file,
            path_in_repo=os.path.basename(json_file),
            repo_id=repo_id,
            token=hf_token
        )
        logging.info(f"Uploaded JSON dataset to Hugging Face repository: {repo_id}")

        print("Writing README.md...")
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print("Uploading README.md...")
        upload_file(
            path_or_fileobj="README.md",
            path_in_repo="README.md",
            repo_id=repo_id,
            token=hf_token
        )
        logging.info(f"Uploaded README.md to Hugging Face repository: {repo_id}")

        print(f"Dataset uploaded to https://huggingface.co/datasets/{repo_id}")
    except Exception as e:
        logging.error(f"Failed to upload to Hugging Face: {e}")
        print(f"Failed to upload to Hugging Face: {e}")

def main():
    readme_content = """
# Pop Lyrics Dataset (Up to 1,000 Songs)

This dataset contains up to 1,000 pop songs with their lyrics, songwriters, genres, and other relevant metadata. The data was collected from Spotify and Genius.

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

## Acknowledgements

- [Spotify](https://www.spotify.com) for providing track information.
- [Genius](https://genius.com) for providing song lyrics.
- [Hugging Face](https://huggingface.co) for hosting the dataset.

## License

This dataset is licensed under the [MIT License](LICENSE).
    """

    upload_dataset_to_huggingface(DATASET_JSON, readme_content, REPO_NAME, HF_TOKEN)

if __name__ == "__main__":
    main()
