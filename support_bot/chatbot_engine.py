# support_bot/chatbot_engine.py
from __future__ import annotations
import logging
import threading
from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("[%(levelname)s] %(asctime)s %(name)s: %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# ---- BASE_DIR (dans Django) ----
try:
    from django.conf import settings
    BASE_DIR = Path(settings.BASE_DIR)
except Exception:
    BASE_DIR = Path(__file__).resolve().parents[1]  # fallback hors Django

# ---- Chemins projet ----
DATA_DIR = BASE_DIR / "support_bot" / "data"
MODEL_DIR = BASE_DIR / "support_bot" / "models"
FAQ_CSV = DATA_DIR / "faq.csv"
# --- CHEMINS POUR LE CLASSIFIEUR TF-IDF ---
VEC_PATH = DATA_DIR / "vectorizer.pkl"
CLF_PATH = DATA_DIR / "model.pkl"

# ---- Imports optionnels ----
# --- Désactivation des imports lourds ---
HAVE_FAISS = False
faiss = None
SentenceTransformer = None

try:
    from sklearn.neighbors import NearestNeighbors
    HAVE_SKLEARN = True
except Exception:
    HAVE_SKLEARN = False

import joblib  # noqa: E402

# ---- États globaux ----
_lock = threading.Lock()
_df: Optional[pd.DataFrame] = None
_init_error: Optional[Exception] = None

# classifieur supervisé (TF-IDF + LogReg où la classe == réponse)
_vec = None
_clf = None
CLF_THRESHOLD = 0.55  # seuil de confiance minimum

# ---- Utils ----
def _ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

def _load_classifier():
    """Charge vectorizer + model s'ils existent (supervisé)."""
    global _vec, _clf
    
    if not VEC_PATH.exists():
        logger.warning("Fichier vectorizer.pkl introuvable ici: %s", VEC_PATH)
        raise FileNotFoundError(f"Fichier vectorizer.pkl introuvable: {VEC_PATH}")
        
    if not CLF_PATH.exists():
        logger.warning("Fichier model.pkl introuvable ici: %s", CLF_PATH)
        raise FileNotFoundError(f"Fichier model.pkl introuvable: {CLF_PATH}")

    try:
        _vec = joblib.load(VEC_PATH)
        _clf = joblib.load(CLF_PATH)
        logger.info("Classifieur chargé (vectorizer.pkl + model.pkl).")
    except Exception as e:
        logger.exception("Échec chargement classifieur: %s", e)
        raise e

def _try_classifier(q: str) -> Tuple[Optional[str], float]:
    """Retourne (réponse_predite, confiance) si classifieur dispo, sinon (None, 0)."""
    if _vec is None or _clf is None or not hasattr(_clf, "predict_proba"):
        logger.warning("Classifieur non chargé, _try_classifier échoue.")
        return None, 0.0
    try:
        X = _vec.transform([q])
        probs = _clf.predict_proba(X)[0]
        y = _clf.classes_[int(np.argmax(probs))]
        conf = float(np.max(probs))
        ans = str(y).strip()
        if ans:
            return ans, conf
        return None, conf
    except Exception as e:
        logger.warning("Classifieur: erreur prédiction (%s)", e)
        return None, 0.0

def _lazy_load():
    """Charge FAQ/embeddings/index/modèles (thread-safe)."""
    global _df, _init_error

    # Vérifie si c'est déjà chargé
    if _df is not None and _vec is not None and _clf is not None and _init_error is None:
        return
    with _lock:
        if _df is not None and _vec is not None and _clf is not None and _init_error is None:
            return
        
        try:
            _ensure_dirs()
            # 1) Lire FAQ (On en a besoin pour les réponses du classifieur)
            if not FAQ_CSV.exists():
                raise FileNotFoundError(
                    f"Fichier FAQ introuvable: {FAQ_CSV}. Crée/pose un CSV 'question,answer'."
                )
            df = pd.read_csv(FAQ_CSV)
            if not {"question", "answer"}.issubset(df.columns):
                raise ValueError("Le CSV doit contenir les colonnes 'question' et 'answer'.")
            
            # ... (Nettoyage du dataframe) ...
            df = df.dropna(subset=["question", "answer"]).astype({"question": str, "answer": str})
            df["question"] = df["question"].str.strip()
            df["answer"] = df["answer"].str.strip()
            df = df[(df["question"].str.len() > 3) & (df["answer"].str.len() > 3)]
            df = df.drop_duplicates(subset=["question"]).reset_index(drop=True)
            _df = df

            # 2) Classifieur supervisé (MAINTENANT OBLIGATOIRE)
            _load_classifier()
            
            # 3), 4) et 5) SONT DESACTIVÉS POUR ÉCONOMISER LA RAM
            # (sentence-transformers, embeddings, et FAISS ne sont pas chargés)

            logger.info("KB prête (Mode Classifieur TF-IDF Seulement): %d entrées.", len(_df))

        except Exception as e:
            _init_error = e
            logger.exception("Erreur d'initialisation chatbot: %s", e)

# ---- API publique ----
def get_chatbot_response(user_input: str) -> str:
    """Modifié: utilise UNIQUEMENT le classifieur supervisé (TF-IDF)."""
    try:
        q = (user_input or "").strip()
        if not q:
            return "Pouvez-vous préciser votre question ?"

        _lazy_load()
        if _init_error:
            # Si _load_classifier a échoué (ex: fichiers .pkl absents)
            logger.error("Erreur lazy_load: %s", _init_error)
            return f"Le chatbot n'est pas prêt: {_init_error}"

        # 1) Classifieur (Seule méthode)
        ans, conf = _try_classifier(q)
        
        if ans and conf >= CLF_THRESHOLD:
            return ans
        else:
            # 2) Fallback (Réponse par défaut)
            logger.info("Réponse non trouvée (confiance: %.2f)", conf)
            return "Je n'ai pas bien compris votre question. Pouvez-vous la reformuler différemment ?"

    except Exception as e:
        logger.exception("CHAT ERROR: %s", e)
        return "Désolé, une erreur s'est produite. Réessayez ou reformulez votre question."

def reload_kb() -> str:
    """Forcer le rechargement (après mise à jour de faq.csv / modèles)."""
    global _df, _init_error, _vec, _clf
    with _lock:
        _df = None
        _init_error = None
        _vec = None
        _clf = None
    _lazy_load()
    return "Rechargé (Mode TF-IDF)." if _init_error is None else f"Échec: {_init_error}"
# ---- Fin du module chatbot_engine.py ----