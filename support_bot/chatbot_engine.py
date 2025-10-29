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
DATA_DIR   = BASE_DIR / "support_bot" / "data"
MODEL_DIR  = BASE_DIR / "support_bot" / "models"
FAQ_CSV    = DATA_DIR / "faq.csv"
EMB_CACHE  = MODEL_DIR / "faq_embeddings.npy"
FAISS_IDX  = MODEL_DIR / "faq.index"  # si FAISS dispo
DEFAULT_ST = "sentence-transformers/all-MiniLM-L6-v2"

# ---- Imports optionnels ----
HAVE_FAISS = False
try:
    import faiss  # type: ignore
    HAVE_FAISS = True
except Exception:
    faiss = None

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception as e:
    logger.error("sentence-transformers absent: %s", e)
    SentenceTransformer = None  # type: ignore

try:
    from sklearn.neighbors import NearestNeighbors  # fallback
    HAVE_SKLEARN = True
except Exception:
    HAVE_SKLEARN = False

import joblib

# ---- États globaux ----
_lock = threading.Lock()
_df: Optional[pd.DataFrame] = None
_model_st: Optional[SentenceTransformer] = None
_index = None  # FAISS ou NearestNeighbors
_init_error: Optional[Exception] = None

# classifieur supervisé (TF-IDF + LogReg où la classe == réponse)
_vec = None
_clf = None
CLF_THRESHOLD = 0.55  # seuil de confiance minimum

# ---- Utils ----
def _ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

def _encode_texts(texts: List[str]) -> np.ndarray:
    """Encode et normalise en float32 (attendu par FAISS)."""
    vecs = _model_st.encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    if isinstance(vecs, list):
        vecs = np.asarray(vecs, dtype=np.float32)
    return vecs.astype("float32")

def _build_index(emb: np.ndarray):
    global _index
    dim = emb.shape[1]
    if HAVE_FAISS:
        logger.info("Construction FAISS IndexFlatIP (dim=%d) ...", dim)
        idx = faiss.IndexFlatIP(dim)
        idx.add(emb)
        _index = idx
        return
    if not HAVE_SKLEARN:
        raise RuntimeError("Aucun moteur d'index dispo (ni FAISS ni scikit-learn).")
    logger.info("Construction NearestNeighbors(metric='cosine') ...")
    nn = NearestNeighbors(metric="cosine")
    nn.fit(emb)
    _index = nn

def _search(qv: np.ndarray, top_k: int) -> Tuple[np.ndarray, np.ndarray]:
    """Retourne (scores, indices). Scores ~ cos_sim (plus grand = plus proche)."""
    if HAVE_FAISS and hasattr(_index, "search"):
        D, I = _index.search(qv.reshape(1, -1), top_k)
        return D[0], I[0]
    # sklearn: distances cos in [0..2]; sim = 1 - dist
    distances, idxs = _index.kneighbors(qv.reshape(1, -1), n_neighbors=top_k)
    sims = 1.0 - distances[0]
    return sims, idxs[0]

def _load_classifier():
    """Charge vectorizer + model s'ils existent (supervisé)."""
    global _vec, _clf
    vec_path = DATA_DIR / "vectorizer.pkl"
    clf_path = DATA_DIR / "model.pkl"
    if vec_path.exists() and clf_path.exists():
        try:
            _vec = joblib.load(vec_path)
            _clf = joblib.load(clf_path)
            logger.info("Classifieur chargé (vectorizer.pkl + model.pkl).")
        except Exception as e:
            logger.warning("Échec chargement classifieur: %s", e)

def _try_classifier(q: str) -> Tuple[Optional[str], float]:
    """Retourne (réponse_predite, confiance) si classifieur dispo, sinon (None, 0)."""
    if _vec is None or _clf is None or not hasattr(_clf, "predict_proba"):
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
    global _df, _model_st, _index, _init_error

    if _df is not None and _model_st is not None and _index is not None and _init_error is None:
        return
    with _lock:
        if _df is not None and _model_st is not None and _index is not None and _init_error is None:
            return
        try:
            _ensure_dirs()
            # 1) Lire FAQ
            if not FAQ_CSV.exists():
                raise FileNotFoundError(
                    f"Fichier FAQ introuvable: {FAQ_CSV}. Crée/pose un CSV 'question,answer'."
                )
            df = pd.read_csv(FAQ_CSV)
            if not {"question", "answer"}.issubset(df.columns):
                raise ValueError("Le CSV doit contenir les colonnes 'question' et 'answer'.")
            df = df.dropna(subset=["question", "answer"]).astype({"question": str, "answer": str})
            df["question"] = df["question"].str.strip()
            df["answer"]   = df["answer"].str.strip()
            df = df[(df["question"].str.len() > 3) & (df["answer"].str.len() > 3)]
            df = df.drop_duplicates(subset=["question"]).reset_index(drop=True)
            _df = df

            # 2) Classifieur supervisé (optionnel)
            _load_classifier()

            # 3) SentenceTransformer
            if SentenceTransformer is None:
                raise RuntimeError("sentence-transformers non disponible.")
            logger.info("Chargement modèle ST: %s", DEFAULT_ST)
            _model_st = SentenceTransformer(DEFAULT_ST)

            # 4) Embeddings (cache conscient de la taille)
            emb = None
            if EMB_CACHE.exists():
                try:
                    e = np.load(EMB_CACHE).astype("float32")
                    if e.shape[0] == len(_df):
                        logger.info("Chargement cache embeddings: %s", EMB_CACHE)
                        emb = e
                    else:
                        logger.warning("Cache embeddings (%d) != lignes CSV (%d) -> recalcul.", e.shape[0], len(_df))
                except Exception as ex:
                    logger.warning("Échec lecture cache embeddings (%s) -> recalcul.", ex)

            if emb is None:
                logger.info("Encodage des questions (%d)...", len(_df))
                emb = _encode_texts(_df["question"].tolist())
                try:
                    np.save(EMB_CACHE, emb)
                    logger.info("Embeddings sauvegardés: %s", EMB_CACHE)
                except Exception as ex:
                    logger.warning("Impossible de sauvegarder embeddings (%s).", ex)

            # 5) Index
            if HAVE_FAISS and FAISS_IDX.exists():
                try:
                    faiss_idx = faiss.read_index(str(FAISS_IDX))
                    if getattr(faiss_idx, "ntotal", 0) != emb.shape[0]:
                        logger.warning("Index FAISS (%d) != nb embeddings (%d) -> reconstruction.", faiss_idx.ntotal, emb.shape[0])
                        _build_index(emb)
                        try:
                            faiss.write_index(_index, str(FAISS_IDX))
                        except Exception:
                            pass
                    else:
                        _index = faiss_idx
                except Exception as e:
                    logger.warning("Échec chargement index FAISS (%s), reconstruction ...", e)
                    _build_index(emb)
                    try:
                        faiss.write_index(_index, str(FAISS_IDX))
                    except Exception:
                        pass
            else:
                _build_index(emb)
                # on sauvegarde l’index FAISS seulement si FAISS est actif
                if HAVE_FAISS:
                    try:
                        faiss.write_index(_index, str(FAISS_IDX))
                    except Exception:
                        pass

            logger.info("KB prête: %d entrées.", len(_df))

        except Exception as e:
            _init_error = e
            logger.exception("Erreur d'initialisation chatbot: %s", e)

# ---- API publique ----
def get_chatbot_response(user_input: str) -> str:
    """Hybride: classifieur supervisé (si conf >= seuil) sinon RAG sémantique."""
    try:
        q = (user_input or "").strip()
        if not q:
            return "Pouvez-vous préciser votre question ?"

        _lazy_load()
        if _init_error:
            return f"Le chatbot n'est pas prêt: {_init_error}"

        # 1) Classifieur (si dispo)
        ans, conf = _try_classifier(q)
        if ans and conf >= CLF_THRESHOLD:
            return ans

        # 2) Fallback RAG (recherche sémantique)
        if _df is None or _index is None or _model_st is None:
            return "Système de recherche indisponible pour le moment."

        qv = _encode_texts([q])[0]  # (d,)
        k = min(12, len(_df))
        sims, idxs = _search(qv, k)
        # filtrer indices invalides
        idxs = [int(i) for i in (idxs.tolist() if hasattr(idxs, "tolist") else list(idxs)) if i >= 0]
        if not idxs:
            return "Je n'ai rien trouvé de pertinent pour l’instant."

        cand = _df.iloc[idxs].copy()
        answer = str(cand.iloc[0].get("answer", "")).strip()
        if not answer:
            return "Je n’ai pas encore la réponse à cette question."
        return answer

    except Exception as e:
        logger.exception("CHAT ERROR: %s", e)
        return "Désolé, une erreur s'est produite. Réessayez ou reformulez votre question."

def reload_kb() -> str:
    """Forcer le rechargement (après mise à jour de faq.csv / modèles)."""
    global _df, _model_st, _index, _init_error, _vec, _clf
    with _lock:
        _df = None
        _model_st = None
        _index = None
        _init_error = None
        _vec = None
        _clf = None
    _lazy_load()
    return "Rechargé." if _init_error is None else f"Échec: {_init_error}"
# ---- Fin du module chatbot_engine.py ----