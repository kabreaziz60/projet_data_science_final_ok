from __future__ import annotations
from pathlib import Path
import pandas as pd, json, re, csv, io

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
RAW  = DATA / "raw"
OUT  = DATA / "faq.csv"

Q_CAND = {"question","q","pattern","patterns","utterance","title","titre","heading","topic","subject","query","ask","prompt","intitule"}
A_CAND = {"answer","a","response","reponse","content","texte","text","body","solution","steps","description","reply","details","paragraph","snippet","summary","note"}

def strip_html(s:str)->str:
    s = re.sub(r"<(script|style).*?</\\1>", " ", str(s), flags=re.S|re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    return s

def clean(s:str)->str:
    s = strip_html(s)
    s = re.sub(r"\s+"," ", s).strip()
    return s

def endq(q:str)->str:
    q = clean(q)
    return q if q.endswith("?") else q + " ?"

def read_csv_aggr(p:Path)->pd.DataFrame:
    encs = ["utf-8-sig","utf-8","cp1252","latin-1"]
    for enc in encs:
        try:
            raw = p.read_bytes()
            sample = raw[:8192].decode(enc, errors="ignore")
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t,")
                sep = dialect.delimiter
            except Exception:
                sep = ";" if sample.count(";")>sample.count(",") else ( "|" if sample.count("|")>sample.count(",") else ("\t" if sample.count("\t")>0 else ",") )
            df = pd.read_csv(io.BytesIO(raw), encoding=enc, sep=sep, engine="python")
            if not df.empty: return df
        except Exception:
            continue
    return pd.DataFrame()

def read_json_aggr(p:Path)->pd.DataFrame:
    encs = ["utf-8-sig","utf-8","cp1252","latin-1"]
    for enc in encs:
        try:
            txt = p.read_text(encoding=enc, errors="ignore")
            try:
                obj = json.loads(txt)
            except Exception:
                obj = [json.loads(l) for l in txt.splitlines() if l.strip()]
            return pd.json_normalize(obj, max_level=2)
        except Exception:
            continue
    return pd.DataFrame()

def first_nonempty(d:dict, keys:set[str])->str:
    for k in keys:
        if k in d and pd.notna(d[k]):
            s = clean(d[k])
            if s: return s
    return ""

def as_list(x):
    if x is None: return []
    if isinstance(x, list): return x
    if isinstance(x, str) and x.strip().startswith("[") and x.strip().endswith("]"):
        try: return json.loads(x)
        except Exception: return [x]
    return [x]

def harvest_df(df:pd.DataFrame)->list[dict]:
    if df.empty: return []
    df = df.copy()
    df.columns = [str(c).lower().strip() for c in df.columns]
    pairs = []

    # intents.json-like
    if "intents" in df.columns and len(df)==1 and isinstance(df.iloc[0]["intents"], list):
        for it in df.iloc[0]["intents"]:
            patt = as_list(it.get("patterns"))
            resp = as_list(it.get("responses") or it.get("response"))
            ans  = clean(resp[0] if resp else "")
            for p in patt:
                q = clean(p)
                if q and ans: pairs.append({"question": endq(q), "answer": ans})
        return pairs

    for _, row in df.iterrows():
        r = {k: row[k] for k in df.columns}

        # patterns = liste → plusieurs Q pour la même réponse
        if isinstance(r.get("patterns"), (list, tuple)):
            ans = first_nonempty(r, A_CAND)
            for pat in r["patterns"]:
                q = clean(pat)
                if q and ans:
                    pairs.append({"question": endq(q), "answer": clean(ans)})
            if ans: continue

        q = first_nonempty(r, Q_CAND)
        a = first_nonempty(r, A_CAND)

        if q and a:
            pairs.append({"question": endq(q), "answer": clean(a)})
            continue

        title = first_nonempty(r, {"title","titre","heading","topic","subject"})
        content = first_nonempty(r, A_CAND | {"content_html","html","markdown","md","texte","text"})
        if title and content:
            pairs.append({"question": endq(title), "answer": clean(content)})
            continue

        if content:
            pairs.append({"question": endq("Informations utiles"), "answer": clean(content)})

    return pairs

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    all_pairs = []

    # 1) prendre aussi faq_ifoad_support_large.csv comme source
    seed = DATA / "raw" / "faq_ifoad_support_large.csv"
    if seed.exists():
        try:
            df = read_csv_aggr(seed)
            if not df.empty and set(["question","answer"]).issubset(df.columns):
                print(f"→ seed: {len(df)}")
                all_pairs.extend(df[["question","answer"]].to_dict("records"))
        except Exception:
            pass

    # 2) moissonner tout le répertoire raw/
    for p in RAW.glob("**/*"):
        if p.name == "faq_ifoad_support_large.csv": 
            continue
        if p.suffix.lower()==".csv":
            df = read_csv_aggr(p)
        elif p.suffix.lower()==".json":
            df = read_json_aggr(p)
        else:
            continue

        if df is None or df.empty:
            print(f"→ {p.name}: 0")
            continue
        pairs = harvest_df(df)
        print(f"→ {p.name}: {len(pairs)}")
        all_pairs.extend(pairs)

    if not all_pairs:
        print("⚠️ Aucun contenu exploitable.")
        return

    faq = pd.DataFrame(all_pairs)
    faq["question"] = faq["question"].map(clean)
    faq["answer"]   = faq["answer"].map(clean)
    faq = faq[(faq["question"].str.len()>5) & (faq["answer"].str.len()>10)]

    faq["q_norm"] = faq["question"].str.lower().str.replace(r"\s+"," ",regex=True).str.strip()
    faq = faq.drop_duplicates(subset=["q_norm"]).drop(columns=["q_norm"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    faq.to_csv(OUT, index=False, encoding="utf-8")
    print(f"✅ FAQ générée: {OUT} — {len(faq)} lignes")

if __name__ == "__main__":
    main()
