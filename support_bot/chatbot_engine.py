# support_bot/chatbot_engine.py
# support_bot/chatbot_engine.py

import json
import random
import nltk
import os  # ⬅️ Importer os

# Définir le chemin absolu du fichier
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'data', 'intents.json')

# Utilisez DATA_PATH pour charger le fichier
with open(DATA_PATH, 'r', encoding='utf-8') as f:
    intents_data = json.load(f)


# Simple logique de "Bag of Words" (Sac de mots) pour la correspondance
def tokenize_and_normalize(sentence):
    """Tokenise la phrase et la normalise (minuscules)"""
    tokens = nltk.word_tokenize(sentence.lower(), language='french')
    # On pourrait ajouter le retrait des stop words et la lemmatisation ici
    return tokens

def get_response(user_input):
    user_tokens = set(tokenize_and_normalize(user_input))

    best_match_tag = None
    highest_score = 0

    # Parcourez tous les intents pour trouver le meilleur match
    for intent in intents_data['intents']:
        for pattern in intent['patterns']:
            pattern_tokens = set(tokenize_and_normalize(pattern))

            # Calcule le nombre de mots-clés communs
            common_tokens = user_tokens.intersection(pattern_tokens)
            score = len(common_tokens)

            # Si l'utilisateur pose exactement un pattern, c'est le meilleur score
            if user_input.lower() == pattern.lower():
                return random.choice(intent['responses'])

            # Si c'est un meilleur score de mots-clés
            if score > highest_score:
                highest_score = score
                best_match_tag = intent['tag']

    # Si un match a été trouvé avec un score raisonnable (ex: au moins 1 mot commun)
    if highest_score > 0 and best_match_tag:
        # Trouvez l'intent correspondant au tag
        matched_intent = next(i for i in intents_data['intents'] if i['tag'] == best_match_tag)
        return random.choice(matched_intent['responses'])
    else:
        # Réponse par défaut
        return "Désolé, je n'ai pas compris votre question. Pouvez-vous reformuler ?"