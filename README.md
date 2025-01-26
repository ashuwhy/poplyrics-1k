# PopLyrics-1K: A Multilingual Music Lyrics Dataset 

![Dataset Version](https://img.shields.io/badge/version-1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Hugging Face](https://img.shields.io/badge/🤗-HuggingFace-yellow)

A curated collection of 1,000 popular songs with rich metadata, designed for NLP research and music analysis. Hosted on Hugging Face Datasets.

[Dataset Veiwer](https://huggingface.co/datasets/ashuwhy/poplyrics-1k/viewer/default/train)

## Overview
A structured dataset containing:
- **1000 songs** spanning multiple decades and genres
- **Multilingual lyrics** with cultural diversity considerations
- **Comprehensive metadata**: Artist, album, release date, duration, popularity score, songwriters, and genre tags
- **Primary sources**: Spotify and Genius API integrations

**Example Use Cases**:
- Lyrics generation models
- Sentiment analysis across music eras
- Cross-cultural language pattern studies
- Genre classification systems

## Dataset Structure
```python
Dataset({
    features: [
        'track_name',        # Song title (2-99 characters)
        'album',             # Album name (1-84 characters)
        'release_date',      # ISO 8601 date format
        'song_length',       # MM:SS duration
        'popularity',        # 0-100 score (float64)
        'songwriters',       # List of creators
        'artist',            # Primary performer
        'lyrics',            # Full lyrical content (17-5,390 chars)
        'genre',             # Multiple genre tags
        'featured_artist'    # Collaborative artists
    ],
    num_rows: 1000
})
```

## Quick Start
Install via Hugging Face Datasets:
```python
from datasets import load_dataset

dataset = load_dataset("ashuwhy/poplyrics-1k", split="train")
```

**Sample Access**:
```python
print(dataset[0])
# Output:
# {
#   'track_name': 'Die With A Smile',
#   'artist': 'Lady Gaga',
#   'lyrics': '[Intro: Bruno Mars]\n(Ooh, ooh)...',
#   'genre': ['art pop', 'dance pop', 'pop']
# }
```

## Applications
| Research Area         | Potential Use                          |
|-----------------------|----------------------------------------|
| NLP                   | Text generation, semantic analysis     |
| Musicology            | Cultural trend analysis                |
| Machine Learning      | Multi-modal learning (audio+text)      |

## Contributing
We welcome contributions through:
1. **Data Expansion**: Submit PRs with new song entries
2. **Quality Improvements**: Flag data inconsistencies
3. **Documentation**: Enhance usage examples

**Workflow**:
```bash
git clone https://github.com/ashuwhy/poplyrics-1k.git
git checkout -b feature/your-contribution
git commit -m "[feat] your changes"
git push origin feature/your-contribution
```

## License
- **MIT Licensed** - Free for academic/commercial use with attribution
- **Ethical Note**: Lyrics may contain sensitive content - users assume responsibility for applications
