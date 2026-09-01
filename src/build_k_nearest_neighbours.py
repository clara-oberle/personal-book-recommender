import pandas as pd

def get_eligible_books(df, book_vectors, book_ids):
    """Filter to read/DNF + has_content. Returns vectors, ratings, ids, mean_rating."""
    # align vectors to eligible_df by book_id lookup

    # Keep only books that have usable embedding content
    eligible = df[df["Exclusive Shelf"].isin(["read", "did-not-finish"]) & (df["has_content"] == True) & (df["My Rating"] > 0)].copy()

    mean_rating = df[df["Exclusive Shelf"] == "read"]["My Rating"].mean()

    # Create a mapping from Book Id -> embedding index
    book_id_to_index = {
        str(book_id): i
        for i, book_id in enumerate(book_ids)
    }

    # Keep only books that actually have an embedding
    eligible = eligible[eligible["Book Id"].astype(str).isin(book_id_to_index)].copy()

    # Get embedding indices
    embedding_indices = [book_id_to_index[str(book_id)] for book_id in eligible["Book Id"]]

    # Convert everything to aligned NumPy arrays
    eligible_vectors = book_vectors[embedding_indices]
    eligible_ratings = eligible["My Rating"].to_numpy()
    eligible_ids = eligible["Book Id"].astype(str).to_numpy()
    return eligible_vectors, eligible_ratings, eligible_ids, mean_rating

def score_candidate_knn(candidate_vector, eligible_vectors, eligible_ratings, mean_rating, k=5, exclude_id=None, eligible_ids=None):
    """Score one candidate. exclude_id lets validation skip the candidate matching itself."""
    similarities = eligible_vectors @ candidate_vector

    if exclude_id is not None:
        mask = eligible_ids != exclude_id
        similarities = similarities[mask]
        eligible_ratings = eligible_ratings[mask]

    # k most similar books
    top_k_idx = similarities.argsort()[::-1][:k]
    # substract mean rating to those specific k books and average that
    neighbor_deviations = eligible_ratings[top_k_idx] - mean_rating

    # KNN prediction
    score = neighbor_deviations.mean()

    # Mean similarity of the k neighbours actually used
    mean_similarity = similarities[top_k_idx].mean()

    return score, mean_similarity

def validate_knn(eligible_vectors, eligible_ratings, eligible_ids, mean_rating, k=5):
    """Leave-one-out: predict each rated book from its neighbors, compare to reality."""
    results = []
    for i, book_id in enumerate(eligible_ids):
        predicted, _ = score_candidate_knn(
            eligible_vectors[i], eligible_vectors, eligible_ratings,
            mean_rating, k=k, exclude_id=book_id, eligible_ids=eligible_ids
        )
        actual_deviation = eligible_ratings[i] - mean_rating
        results.append({"Book Id": book_id, "predicted": predicted, "actual": actual_deviation})
    return pd.DataFrame(results)

def score_to_read(to_read_df, to_read_vectors, eligible_vectors, eligible_ratings, mean_rating, k=5):
    """Score real candidates — no exclusion needed, they're not in the eligible set."""
    scores = []
    mean_similarities = []
    for i in range(len(to_read_df)):
        score, mean_similarity = score_candidate_knn(to_read_vectors[i], eligible_vectors, eligible_ratings, mean_rating, k=k)
        scores.append(score)
        mean_similarities.append(mean_similarity)

    to_read_df["knn_score"] = scores
    to_read_df["mean_neighbor_similarity"] = mean_similarities

    to_read_df = to_read_df[to_read_df["has_content"] == True]
    return to_read_df.sort_values("knn_score", ascending=False)

def main():
    return

if __name__ == "__main__":
    main()