# Personal Book Intelligence

A machine-learning project built around my own Goodreads reading history, an exploration of what my ratings actually say about my taste, and how far content-based recommendation can get with a small, personal, multilingual dataset.

I'm a 3rd/4th year Computer Science / Data Science student. Rather than working through another generic Kaggle dataset, I wanted to apply recommendation systems, NLP, and embeddings to data that's actually mine, and to use the process to genuinely understand *why* these methods work, and where they break down, rather than just calling library functions.

This is not a production recommender. It's a personal investigation: given ~185 books I've read and rated, can a system built from content embeddings and my own ratings tell me anything real about my taste, and what does it fail to capture?

## What this project actually explores

- **What do my own ratings and reading habits look like?** — distribution, pace, genre spread, DNF patterns.
- **Can a book's *content* (description, genre/subject tags) predict how much I'd like it?** — and what does "predict" even mean with only ~165 usable data points?
- **Is my taste one coherent thing, or several?** — this turned out to be a central, non-obvious finding of the project (see Results below).
- **When does comparing book content work well, and when does it have problems?** — for example, when there are very few similar books in a genre, when my rating depends on the quality of the writing rather than the book's topic, when different book descriptions use very similar promotional language, or when there is very little information available about a book.

## Data

Starting point: a Goodreads CSV export (~185 books) — ratings, shelves, dates read, ISBNs, page counts, authors, titles, and free-text reviews (written in a mix of Catalan, Spanish, and English).

Goodreads' raw export has real quirks that shaped the cleaning process: a `0` rating means *unrated*, not *zero stars*; ISBNs are wrapped in Excel-formula syntax; some books appear more than once under different titles (e.g. translated editions); dates arrive as strings.

The project uses flat files and in-memory data structures throughout — no database, no ORM. External metadata (descriptions, genre/subject tags) is fetched from the Google Books and Open Library APIs and cached locally as JSON, so books are never re-fetched once resolved.

## Pipeline

**1. EDA** (`notebooks/01_eda`)
Cleaned ratings (resolving the 0-rating ambiguity), parsed dates, cleaned ISBNs, resolved duplicate/mislabeled entries. Found: my ratings skew high (clustered 3–5), no strong page-length bias, and a small but real DNF signal.

**2. Metadata enrichment** (`src/enrich_data.py`)
A two-API pipeline (Google Books for descriptions, Open Library for genre/subject tags) with idempotent local caching, ISBN-first lookup with title/author fallback, and per-source provenance tracking. 165 of 186 books successfully enriched; the remaining 21 fall back to title/author text with an explicit `has_content: False` flag rather than being dropped.

**3. Dataset consolidation** (`src/build_dataset.py`)
Merged enrichment data into one embedding-ready text field per book, with two dedicated cleaning passes: stripping HTML fragments, and filtering out promotional/commercial noise (bestseller-list mentions, movie-tie-in language, award names, library-cataloging tags) that were otherwise inflating similarity scores between unrelated books that merely shared a publisher's marketing boilerplate.

**4. Embeddings** (`src/embed_books.py`, explored in `notebooks/02`–`05`)
Used `paraphrase-multilingual-MiniLM-L12-v2`, chosen specifically to handle the Catalan/Spanish content in my reviews and some descriptions. Verified the resulting space two ways: a nearest-neighbor spot-check (sequels correctly rank as each other's closest match) and a pairwise similarity distribution across the full library, which established that similarities cluster around ~0.32 with a distinct, sparse high-similarity tail, giving a real baseline for what "high similarity" means in this space, rather than treating raw cosine values as meaningful in isolation.

**5. Taste representation & recommendation** (`src/build_taste_vector.py`, `src/build_k_nearest_neighbours.py`, `notebooks/06`)
Built and compared two representations of my taste:

- **Centroid** — a single rating-weighted, mean-centered vector averaged across all rated books.
- **k-Nearest Neighbors** — for each candidate book, its predicted score is derived from the ratings of its *k* most similar already-rated books, computed independently per candidate.

The centroid approach revealed a genuine structural limitation: my taste isn't one coherent direction in embedding space, it's several (fantasy vs. contemporary romance vs. literary fiction), and averaging across them caused real cancellation, books I rated 4–5 stars (*Pride and Prejudice*, *The Nightingale*, several romances) ended up with *negative* similarity to my own centroid. Leave-one-out validation (with a data-leakage bug caught and fixed along the way) confirmed this quantitatively: k-NN clearly outperforms the centroid specifically in the region where the centroid fails, though neither method reaches strong absolute correlation, an honest reflection of the dataset's size and diversity, not a bug to chase away.

## Results & known limitations

- The final k-NN scorer, applied to my `to-read` shelf, produces a ranked, confidence-annotated recommendation list (each candidate carries both a predicted score and the mean similarity of the neighbors it was based on), with low-content and fallback-only books explicitly excluded or flagged rather than silently mixed in.
- **Content embeddings can't see writing quality.** A book I rated low despite genre-matching well against books I loved (weak dialogue, flat characters, per my own review) is a case content-based similarity simply cannot catch, a real, structural ceiling for this class of method, not a tuning problem.
- **Sparse genres force weak matches.** With only ~165 reference books, `k=5` sometimes has to reach for mediocre neighbors in thin regions of the space (e.g. classics, literary fiction I've read little of), producing overconfident scores on weak evidence, visible directly by comparing predicted score against neighbor similarity.
- **Generic promotional language and near-duplicate descriptions are a recurring artifact**, not a one-off bug, caught multiple times across the project (bestseller-list noise, ~0.98 similarity between books sharing identical publisher blurbs) and worth remaining alert to in any future extension.

## Project Structure

```
data/
├── raw/             # Original Goodreads export
├── clean/           # Cleaned CSV from EDA
├── enriched/        # API enrichment cache (enriched + not-enriched)
├── embedding/       # Embedding-ready dataset, book vectors, and taste vector
└── output/          # Saved plots and figures

notebooks/
├── 01_eda
├── 02_check_embeddings_original
├── 03_check_embeddings_updated
├── 04_explore_genres
├── 05_explore_similarity_space
└── 06_compare_taste_vector_kNN

src/
├── enrich_data.py
├── build_dataset.py
├── embed_books.py
├── build_taste_vector.py
└── build_k_nearest_neighbours.py
```

## Tech stack

- Python — pandas / NumPy, scikit-learn, Matplotlib / Seaborn
- `sentence-transformers` (`paraphrase-multilingual-MiniLM-L12-v2`)
- Google Books API, Open Library API
- Jupyter
- Flat files only — no database, no ORM

## Status

The `master` branch represents a finished, working pipeline: raw Goodreads export in, validated content-based recommendations out, with the reasoning and limitations behind each design decision documented in the notebooks. Further exploration, adaptive/threshold-based neighbor selection, recency-weighted taste, incorporating my review text as an additional signal, and eventually mood/context-aware recommendations, will happen on separate branches rather than on `master`.
