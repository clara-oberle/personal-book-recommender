# Personal Book Intelligence

A small machine-learning project built around my personal Goodreads reading data.

I'm a 3rd/4th year Computer Science / Data Science student, and I wanted a lightweight project where I could explore recommendation systems, NLP, and embeddings using data that actually matters to me.

The goal is not to build a production recommendation system. Instead, I want to understand the interesting ML concepts by applying them to my own reading history.

## Goals

### 1. Understand my reading patterns

Start with a short EDA phase using my Goodreads CSV:

* Rating distribution
* Reading pace over time
* Genres and subjects
* DNF patterns
* Page count vs. rating
* Rereads and read count
* Other interesting patterns in my reading history

The EDA is intentionally short — the main focus is the ML side of the project.

### 2. Recommend books I will actually like

Build a content-based recommendation system using book metadata.

The planned approach is roughly:

**Goodreads data → book metadata → text embeddings → representation of my taste → ranked book recommendations**

Book descriptions and genre/subject information will be enriched using external book APIs and converted into embeddings with a pretrained `sentence-transformers` model.

I'll then explore different ways of representing my preferences from my Goodreads ratings and using that representation to rank candidate books.

The goal is not just to make recommendations, but to understand why the methods work and what the limitations are with a small personal dataset.

### 3. Eventually incorporate mood/context

In the future, I want recommendations to take into account how I feel when choosing a book.

For example:

> "I want something cozy and slow."

or

> "I'm anxious and need some escapism."

This is **not part of the initial implementation**.

However, the project should be designed so that contextual information can later be incorporated into the recommendation model without having to rebuild everything from scratch.

## Data

The starting point is a Goodreads CSV export containing information such as:

* Books read
* Ratings
* Shelves
* Dates read
* ISBNs
* Page counts
* Authors
* Titles
* Other Goodreads metadata

The project deliberately uses flat files and in-memory data structures.

There is:

* No database
* No ORM
* No complex infrastructure

External book metadata will be fetched through APIs and cached locally so that the same books do not need to be requested repeatedly.

## Planned approach

1. **EDA**

   * Understand the Goodreads data
   * Identify quirks and missing values
   * Explore reading and rating patterns

2. **Metadata enrichment**

   * Retrieve descriptions and genre/subject information
   * Use ISBN13 where available
   * Cache API results locally

3. **Book embeddings**

   * Combine relevant textual metadata
   * Generate embeddings using a pretrained `sentence-transformers` model
   * Explore what the resulting similarity space represents

4. **Taste representation & recommendation**

   * Use my Goodreads ratings as supervision
   * Experiment with different representations of my preferences
   * Rank candidate books based on similarity and/or learned features

5. **Future: context-aware recommendations**

   * Introduce a context/mood representation
   * Combine book representation with the reader's current context

## Philosophy

This is intentionally a small project.

I want to:

* Understand the concepts rather than just use libraries
* Write the code myself and use review/discussion to improve it
* Get something working quickly
* Go deeper into the interesting ML/NLP parts
* Use my own data rather than a generic Kaggle dataset

The project should stay lean and exploratory rather than becoming a large software-engineering exercise.

## Tech stack

* Python
* pandas / NumPy
* scikit-learn
* Matplotlib / Seaborn
* Open Library / Google Books API
* sentence-transformers
* Jupyter

No database or ORM