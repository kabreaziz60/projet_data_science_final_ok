import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import joblib

# 📁 Définir les chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'chatbot_training_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, '..', 'data', 'model.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, '..', 'data', 'vectorizer.pkl')

# 📦 Charger les données
df = pd.read_csv(DATA_PATH)

# 🧠 Vectorisation des questions
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['question'])

# 🤖 Entraînement du modèle
model = NearestNeighbors(n_neighbors=1, metric='cosine')
model.fit(X)

# 💾 Sauvegarde
joblib.dump(model, MODEL_PATH)
joblib.dump(vectorizer, VECTORIZER_PATH)

print("✅ Modèle entraîné et sauvegardé avec succès.")
