from sentence_transformers import SentenceTransformer
import pandas as pd
import numpy as np

DATA_FOR_EMBEDDING = "data/embedding/embedding_join_clean_df.csv"
EMBEDDINGS_PATH = "data/embedding/embeddings.npy"
BOOK_IDS_PATH = "data/embedding/book_ids.npy"

def main():
    df = pd.read_csv(DATA_FOR_EMBEDDING)

    data = {}

    book_id = df["Book Id"].astype(str).to_numpy()
    text = df["embedding_text"].tolist()

    model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    embeddings = model.encode(text, normalize_embeddings=True)

    np.save(EMBEDDINGS_PATH, embeddings)
    np.save(BOOK_IDS_PATH, book_id)
    
    return

if __name__ == "__main__":
    main()