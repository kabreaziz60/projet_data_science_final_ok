# support_bot/chatbot_engine.py
# VERSION SIMPLIFIÉE (TF-IDF + NearestNeighbors)
# Ce code n'utilise PAS sentence-transformers et est TRÈS LÉGER.
from __future__ import annotations
import logging
import threading
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors

# --- Configuration du Logger ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# --- Configuration des Chemins ---
try:
    from django.conf import settings
    BASE_DIR = Path(settings.BASE_DIR)
    logger.info("Chargement en mode Django. BASE_DIR = %s", BASE_DIR)
except Exception:
    BASE_DIR = Path(__file__).resolve().parents[1]  # fallback hors Django
    logger.info("Chargement en mode non-Django. BASE_DIR = %s", BASE_DIR)

DATA_DIR = BASE_DIR / "support_bot" / "data"
FAQ_CSV = DATA_DIR / "faq.csv"

# --- Constantes du Modèle ---
# Seuil de similarité (de 0.0 à 1.0)
# Si le score est plus bas que ça, le bot dit "Je n'ai pas compris"
# Vous pouvez le baisser à 0.2 ou 0.3 si le bot est trop strict.
SIMILARITY_THRESHOLD = 0.2

# --- États Globaux (pour le cache) ---
_lock = threading.Lock()
_df: Optional[pd.DataFrame] = None
_vectorizer: Optional[TfidfVectorizer] = None
_index: Optional[NearestNeighbors] = None
_question_vectors = None  # C'est la matrice TF-IDF
_init_error: Optional[Exception] = None

def _lazy_load():
    """
    Charge le CSV, entraîne le TfidfVectorizer et l'index NearestNeighbors.
    Ne s'exécute qu'une seule fois au démarrage.
    """
    global _df, _vectorizer, _index, _question_vectors, _init_error

    # Vérifie si c'est déjà chargé
    if _df is not None and _index is not None:
        return
    
    with _lock:
        # Re-vérifie à l'intérieur du 'lock' (au cas où un autre thread attendait)
        if _df is not None and _index is not None:
            return
        
        try:
            logger.info("Démarrage du chargement du modèle léger (TF-IDF)...")
            
            # 1) Vérifier si le dossier data existe
            if not DATA_DIR.exists():
                raise FileNotFoundError(f"Dossier 'data' introuvable: {DATA_DIR}")
            
            # 2) Lire le fichier FAQ (faq.csv)
            if not FAQ_CSV.exists():
                raise FileNotFoundError(f"Fichier FAQ introuvable: {FAQ_CSV}")
            
            logger.info("Lecture de %s...", FAQ_CSV)
            df = pd.read_csv(FAQ_CSV)
            
            # 3) Nettoyer les données (très important)
            if not {"question", "answer"}.issubset(df.columns):
                raise ValueError("Le CSV doit contenir les colonnes 'question' et 'answer'.")
            
            df = df.dropna(subset=["question", "answer"]).astype({"question": str, "answer": str})
            df["question"] = df["question"].str.strip().str.lower() # Mettre en minuscule
            df["answer"] = df["answer"].str.strip()
            df = df.drop_duplicates(subset=["question"]).reset_index(drop=True)
            
            if len(df) == 0:
                raise ValueError("Le fichier 'faq.csv' est valide mais vide après nettoyage.")
            
            _df = df
            logger.info("CSV chargé et nettoyé: %d questions trouvées.", len(_df))

            # 4) Entraîner le Vectorizer (TF-IDF)
            logger.info("Entraînement du TfidfVectorizer...")
            _vectorizer = TfidfVectorizer(stop_words=None) # Vous pouvez changer 'french'
            _question_vectors = _vectorizer.fit_transform(_df["question"])
            
            # 5) Entraîner l'Index de recherche (NearestNeighbors)
            logger.info("Entraînement de l'index NearestNeighbors...")
            _index = NearestNeighbors(n_neighbors=1, metric="cosine")
            _index.fit(_question_vectors)
            
            logger.info("====== CHATBOT PRÊT (Mode Léger) ======")

        except Exception as e:
            _init_error = e
            logger.exception("!!!!!! ERREUR D'INITIALISATION DU CHATBOT !!!!!!: %s", e)

# ---- API publique ----
def get_chatbot_response(user_input: str) -> str:
    """
    Prend une question, la vectorise, et trouve la réponse la plus proche.
    """
    try:
        q = (user_input or "").strip()
        if not q:
            return "Pouvez-vous préciser votre question ?"

        # Charge le modèle s'il n'est pas encore en mémoire
        _lazy_load()

        # Si le chargement a échoué (ex: faq.csv non trouvé)
        if _init_error:
            logger.error("Erreur lazy_load: %s", _init_error)
            # Affiche l'erreur à l'utilisateur pour le débogage
            return f"Le chatbot n'est pas prêt: {_init_error}"
        
        # Si les modèles ne sont pas chargés pour une raison inconnue
        if _vectorizer is None or _index is None or _df is None:
            logger.error("Composants du chatbot non initialisés.")
            return "Désolé, le chatbot n'est pas correctement initialisé."

        # 1. Transformer la question de l'utilisateur
        q_vec = _vectorizer.transform([q.lower()]) # Mettre en minuscule aussi

        # 2. Chercher la question la plus proche dans l'index
        distances, idxs = _index.kneighbors(q_vec, n_neighbors=1)
        
        match_index = idxs[0][0]
        match_distance = distances[0][0]
        
        # 'distance' est la distance cosinus (0 = identique, 1 = opposé)
        # 'similarité' est l'inverse (1 = identique, 0 = opposé)
        match_similarity = 1.0 - match_distance

        # 3. Vérifier si la similarité est suffisante
        if match_similarity >= SIMILARITY_THRESHOLD:
            answer = _df.iloc[match_index]["answer"]
            # Optionnel : logguer le match
            # matched_q = _df.iloc[match_index]["question"]
            # logger.info("Match (Conf: %.2f): '%s' -> '%s'", match_similarity, q, matched_q)
            return str(answer)
        else:
            # 4. Réponse si le score est trop bas
            logger.info("Aucun match (Meilleur score: %.2f < %.2f)", match_similarity, SIMILARITY_THRESHOLD)
            return "Je n'ai pas bien compris votre question. Pouvez-vous la reformuler différemment ?"

    except Exception as e:
        logger.exception("CHAT ERROR: %s", e)
        return "Désolé, une erreur s'est produite. Réessayez ou reformulez votre question."

def reload_kb() -> str:
    """Forcer le rechargement (après mise à jour de faq.csv)."""
    global _df, _vectorizer, _index, _question_vectors, _init_error
    with _lock:
        _df = None
        _vectorizer = None
        _index = None
        _question_vectors = None
        _init_error = None
    
    logger.info("Forçage du rechargement de la base de connaissances...")
    _lazy_load()
    
    if _init_error:
        return f"Échec du rechargement: {_init_error}"
    return "Base de connaissances (TF-IDF) rechargée."
# ---- Fin du module chatbot_engine.py ----