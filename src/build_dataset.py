import pandas as pd
from .enrich_data import load_json_file, save_json_file
import re

DF_PATH = "data/clean/goodreads_clean.csv"
ENRICHED_DATA_PATH = "data/enriched/enriched_books.json"
# NOT_ENRICHED_DATA_PATH = "data/enriched/not_enriched_books.json"

EMBEDDING_DATA_PATH = "data/embedding/embedding_data.json"
EMBEDDING_JOINED_DF_PATH = "data/embedding/embedding_join_clean_df.csv"


def clean_description(text):
    if not text:
        return ""

    # Remove HTML
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove bestseller mentions
    text = re.sub(
        r".*?(#1\s+New York Times Bestseller|USA Today Bestseller|New York Times Book Review|New York Times Bestseller).*?(\.|$)",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Remove movie adaptation mentions
    text = re.sub(
        r".*?(Now a major motion picture|soon to be a movie|Set to be a major movie|New Movie Coming Soon from Amazon MGM Studios).*?(\.|$)",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Remove TikTok mentions
    text = re.sub(
        r".*?TikTok Sensations?.*?(\.|$)",
        " ",
        text,
        flags=re.IGNORECASE
    )

    # Clean up whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text

def main():
    clean_df = pd.read_csv(DF_PATH)
    enriched_data = load_json_file(ENRICHED_DATA_PATH)

    data = {}

    for index, row in clean_df.iterrows():
        book_id = str(row["Book Id"])
        title = row["Title"]
        author= row["Author"]

        if book_id in enriched_data:
            book = enriched_data[book_id]

            google = book["google_books"]
            open_library = book["open_library"]

            google_description = google.get("description")
            open_library_description = open_library.get("description")

            if google_description:
                description = google_description
                content_source = "google"
            elif open_library_description:
                description = open_library_description
                content_source = "open_library"
            else:
                description = ""
                content_source = "enriched_no_description"

            google_categories = google.get("categories") or []

            open_library_subjects = [subject["name"] 
                                     for subject in (open_library.get("subjects") or [])]

            # remove nyt:... tags
            genre_signal = [
                tag for tag in google_categories + open_library_subjects
                if not re.match(r"^nyt:", tag, re.IGNORECASE)
            ]

            # combine and deduplicate categories, cap at 10
            genre_signal = list(dict.fromkeys(genre_signal))[:10]
            
            description = clean_description(description)

            has_content = bool(description or genre_signal)
            if not has_content:
                embedding_text = f"{title} by {author}"
                content_source = "fallback_title_author"
            else:
                if description:
                    if genre_signal:
                        embedding_text = (description + ". Genres: " + ", ".join(genre_signal))
                    else:
                        embedding_text = description

                else:
                    if genre_signal:
                        embedding_text = ("Genres: " + ", ".join(genre_signal))

        else:
            embedding_text = f"{title} by {author}"
            has_content = False
            content_source = "fallback_title_author"

        data[book_id] = {
            "title": title,
            "embedding_text": embedding_text,
            "content_source": content_source,
            "has_content": has_content
            }
        
    save_json_file(EMBEDDING_DATA_PATH, data)
    print(f"Saved {len(data)} books to {EMBEDDING_DATA_PATH}")

    # join with dataframe
    embedding_df = pd.DataFrame.from_dict(data, orient="index")

    embedding_df.index.name = "Book Id"
    embedding_df = embedding_df.reset_index()
    embedding_df = embedding_df.drop(columns="title")

    clean_df["Book Id"] = clean_df["Book Id"].astype(str)
    embedding_df["Book Id"] = embedding_df["Book Id"].astype(str)

    df_embedded = clean_df.merge(embedding_df, on="Book Id", how="left")
    df_embedded.to_csv(EMBEDDING_JOINED_DF_PATH, index=False)

    return

if __name__ == "__main__":
    main()