import os, numpy as np, pandas as pd, faiss
from tqdm import tqdm
from sentence_transformers import SentenceTransformer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CORPUS = os.path.join(DATA_DIR, "qa_corpus.csv")
ROWS = os.path.join(DATA_DIR, "qa_rows.parquet")
INDEX = os.path.join(DATA_DIR, "faiss.index")
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # FR OK

def run():
  df = pd.read_csv(CORPUS)
  model = SentenceTransformer(MODEL_NAME)
  qs = df["question"].tolist()

  # embeddings normalisés → cosine = dot product
  print("🔎 Encodage des questions…")
  emb = model.encode(qs, batch_size=64, normalize_embeddings=True, show_progress_bar=True)
  emb = emb.astype("float32")

  # sauvegardes
  df.to_parquet(ROWS, index=False)
  d = emb.shape[1]
  index = faiss.IndexFlatIP(d)
  index.add(emb)
  faiss.write_index(index, INDEX)
  print(f"✅ FAISS index: {index.ntotal} vectors → {INDEX}")
  print(f"✅ Lignes: {len(df)} → {ROWS}")

if __name__ == "__main__":
  run()
