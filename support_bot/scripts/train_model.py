# support_bot/scripts/train_model.py
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction import text
import joblib

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
FAQ  = DATA / "faq.csv"

# 1) Charger & nettoyer
df = pd.read_csv(FAQ)
df = df.dropna(subset=["question", "answer"]).astype({"question": str, "answer": str})
df["question"] = df["question"].str.strip()
df["answer"]   = df["answer"].str.strip()
df = df[(df["question"].str.len() > 3) & (df["answer"].str.len() > 3)]
df = df.drop_duplicates(subset=["question"]).reset_index(drop=True)
print("Taille du dataset:", len(df))

# 2) Stopwords FR (compatible scikit-learn >= 1.5)
french_stop = set(text.ENGLISH_STOP_WORDS).union({
    "le","la","les","un","une","de","des","du","et","ou","en","au","aux","à","pour",
    "ce","cet","cette","ces","dans","sur","par","avec","sans","plus","moins","ne","pas",
    "je","tu","il","elle","nous","vous","ils","elles","mon","ma","mes","ton","ta","tes",
    "son","sa","ses","leur","leurs","que","quoi","qui","dont","où","comme","quand","afin",
    "être","avoir","faire","peut","peux","suis","est","sont","était","étaient","sera"
})
# >>> convertir en LISTE (pas frozenset)
french_stop = list(french_stop)

# 3) Vectoriser
vectorizer = TfidfVectorizer(
    stop_words=french_stop,
    sublinear_tf=True,
    ngram_range=(1, 2),
)
X = vectorizer.fit_transform(df["question"])
y = df["answer"]

# 4) Entraîner
clf = LogisticRegression(max_iter=500, solver="lbfgs", multi_class="auto")
clf.fit(X, y)

# 5) Sauvegarder
joblib.dump(vectorizer, DATA / "vectorizer.pkl")
joblib.dump(clf, DATA / "model.pkl")
print("✅ Modèle entraîné: vectorizer.pkl & model.pkl")
