import os
import pandas as pd

# 📁 Définir le chemin du fichier source
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, '..', 'data', 'support_wifi_dataset.csv')

# 📦 Charger les données
df = pd.read_csv(DATA_PATH)

# 🧹 Nettoyage
df = df.drop_duplicates(subset=['titre', 'contenu'])
df = df[df['contenu'].str.strip() != '']

# 🧠 Structuration en question-réponse
df['question'] = df['titre'].apply(lambda x: f"{x.strip()} ?")
df['réponse'] = df['contenu'].str.strip()

# 💾 Sauvegarde
OUTPUT_PATH = os.path.join(BASE_DIR, '..', 'data', 'chatbot_training_data.json')
df[['question', 'réponse']].to_csv(OUTPUT_PATH, index=False)

print("✅ Dataset nettoyé et structuré avec succès.")
