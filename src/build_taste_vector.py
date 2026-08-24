import numpy as np
import pandas as pd

BOOK_ID_PATH = "/home/claraoberle/personal-book-recommender/data/embedding/book_ids.npy"
EMBEDDINGD_PATH = "/home/claraoberle/personal-book-recommender/data/embedding/embeddings.npy"
CLEAN_DF_JOIN_EMBEDDINGS_PATH = "/home/claraoberle/personal-book-recommender/data/embedding/embedding_join_clean_df.csv"
TASTE_VECTOR_PATH = "/home/claraoberle/personal-book-recommender/data/embedding/taste_vector.npy"

def build_taste_vector(df, book_vectors, book_ids):
    # Keep only books that have usable embedding content
    eligible = df[df["Exclusive Shelf"].isin(["read", "did-not-finish"]) & (df["has_content"] == True)].copy()

    # Mean rating is calculated only from read books
    read_books = eligible[eligible["Exclusive Shelf"] == "read"]

    mean_rating = read_books["My Rating"].mean()

    # Remove books without a rating (only applies to did-not-finish, all read books have ratings)
    eligible = eligible[eligible["My Rating"] > 0].copy()

    # Calculate weight = rating - mean rating
    eligible["weight"] = eligible["My Rating"] - mean_rating

    # Create a mapping from Book Id -> embedding index
    book_id_to_index = {
        str(book_id): i
        for i, book_id in enumerate(book_ids)
    }

    # Accumulate weighted embeddings
    weighted_sum = np.zeros(book_vectors.shape[1])

    denominator = 0.0

    for _, row in eligible.iterrows():
        book_id = str(row["Book Id"])

        if book_id not in book_id_to_index:
            continue

        embedding_index = book_id_to_index[book_id]
        vector = book_vectors[embedding_index]
        weight = row["weight"]

        weighted_sum += weight * vector
        denominator += abs(weight)

    # Avoid division by zero
    if denominator == 0:
        raise ValueError("All book weights are zero. Cannot build taste vector.")

    # Weighted average
    taste_vector = weighted_sum / denominator

    # Renormalize to unit length
    norm = np.linalg.norm(taste_vector)

    if norm == 0:
        raise ValueError("Taste vector has zero norm and cannot be normalized.")

    taste_vector = taste_vector / norm

    return taste_vector

def main():
    df = pd.read_csv(CLEAN_DF_JOIN_EMBEDDINGS_PATH)
    embeddings = np.load(EMBEDDINGD_PATH, allow_pickle=True)
    book_ids = np.load(BOOK_ID_PATH, allow_pickle=True)

    taste_vector = build_taste_vector(df, embeddings, book_ids)
    
    np.save(TASTE_VECTOR_PATH, taste_vector)
    
    print(f"Taste vector saved to: {TASTE_VECTOR_PATH}")
    print(f"Shape: {taste_vector.shape}")
    print(f"Norm: {np.linalg.norm(taste_vector):.6f}")

    return

if __name__ == "__main__":
    main()