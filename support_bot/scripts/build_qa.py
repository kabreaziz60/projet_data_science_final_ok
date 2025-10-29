import os, re, uuid, pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW = os.path.join(DATA_DIR, "support_dataset_raw.csv")
OUT = os.path.join(DATA_DIR, "qa_corpus.csv")

INTENT_RULES = [
  ("wifi|réseau|internet|wlan", "wifi"),
  ("imprimante|print", "imprimante"),
  ("mise.?à.?jour|windows update|update", "windows"),
  ("installer|installation|setup|msi|exe", "installation_logiciel"),
  ("navigateur|firefox|chrome|edge", "navigateur"),
  ("antivirus|sécurité|protection", "securite"),
]

TEMPLATES = [
  "Comment {base} ?",
  "Que faire pour {base} ?",
  "Pourquoi {base} ne fonctionne pas ?",
  "Tutoriel : {base} ?",
  "Guide débutant : {base} ?",
  "Problème : {base}. Comment résoudre ?",
  "Solution rapide pour {base} ?",
  "Étapes pour {base} ?",
  "Je n’arrive pas à {base}, que faire ?",
]

def guess_intent(text):
  low=text.lower()
  for pat, intent in INTENT_RULES:
    if re.search(pat, low): return intent
  return "depannage_pc"

def base_from_title(title):
  t = re.sub(r"^\s*(\[.*?\]\s*)", "", str(title)).strip()
  t = re.sub(r"\s+", " ", t)
  # on retire certains débuts “Résoudre … / Dépanner …”
  t = re.sub(r"^(résoudre|réparer|dépanner)\s+les?\s+probl(è|e)mes?\s+de\s+", "", t, flags=re.I)
  return t

def run():
  raw = pd.read_csv(RAW)
  rows=[]
  for _, r in raw.iterrows():
    base = base_from_title(r["titre"])
    intent = guess_intent(str(r["titre"])+" "+str(r["contenu"]))
    answer = str(r["contenu"]).strip()
    source = r["source"]
    tags = intent

    # variations
    for tpl in TEMPLATES:
      q = tpl.format(base=base)
      rows.append({
        "id": str(uuid.uuid4()),
        "question": q,
        "answer": answer,
        "intent": intent,
        "tags": tags,
        "source": source,
        "lang": "fr"
      })
    # question brute
    rows.append({
      "id": str(uuid.uuid4()),
      "question": base + " ?",
      "answer": answer,
      "intent": intent,
      "tags": tags,
      "source": source,
      "lang": "fr"
    })

  df = pd.DataFrame(rows).drop_duplicates(subset=["question","answer"])
  df.to_csv(OUT, index=False)
  print(f"✅ Corpus Q/A: {len(df)} lignes → {OUT}")

if __name__ == "__main__":
  run()
