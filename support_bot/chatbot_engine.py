import os
import joblib
import pandas as pd

# 📁 Définir les chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'data', 'model.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'data', 'vectorizer.pkl')
TRAINING_DATA_PATH = os.path.join(BASE_DIR, 'data', 'chatbot_training_data.csv')

# 📦 Charger le modèle et les données
model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)
df = pd.read_csv(TRAINING_DATA_PATH)

# 🤖 Moteur TF-IDF : retourne la réponse la plus proche
def get_chatbot_response(user_input):
    try:
        vect = vectorizer.transform([user_input])
        _, indices = model.kneighbors(vect)
        response = df.iloc[indices[0][0]]['réponse']
        return response
    except Exception as e:
        return "Désolé, je n'ai pas compris votre question. Pouvez-vous reformuler ?"
