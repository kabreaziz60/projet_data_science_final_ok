import os, time, requests, pandas as pd
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0"}

MS_URLS = [
  "https://support.microsoft.com/fr-fr/windows/r%C3%A9soudre-les-probl%C3%A8mes-de-connexion-wi-fi-dans-windows-9424a1f7-6a3b-65a6-4d78-7f07eee84d2c",
  "https://support.microsoft.com/fr-fr/windows/windows-update-faq-16c42daf-2354-8e08-5df9-9d6a3a5b1a45",
  "https://support.microsoft.com/fr-fr/windows/r%C3%A9parer-les-probl%C3%A8mes-d-imprimante-dans-windows-10-ecfe4daf-0b2c-0b7a-4350-76d6f2f7a6f5",
]

VENDOR_URLS = [
  ("lenovo","https://support.lenovo.com/fr/fr/solutions/ht502846-windows-10-wifi-troubleshooting"),
  ("hp","https://support.hp.com/fr-fr/help/diagnostics/wireless-network-and-internet"),
  ("dell","https://www.dell.com/support/kbdoc/fr-fr/000124630/windows-10-r%C3%A9solution-des-probl%C3%A8mes-de-r%C3%A9seau-sans-fil"),
  ("mozilla","https://support.mozilla.org/fr/kb/resoudre-les-problemes-de-connexion"),
]

def scrape_generic(url):
  try:
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find(["h1","h2"])
    blocks = soup.select("h2, h3, p, li")
    buf=[]
    for b in blocks:
      t = " ".join(b.get_text(" ", strip=True).split())
      if len(t) >= 40:
        buf.append(t)
    if title and buf:
      return {"source": url, "titre": title.get_text(strip=True), "contenu": "\n".join(buf)}
  except Exception:
    return None
  return None

def run():
  rows=[]
  for url in MS_URLS:
    item = scrape_generic(url)
    if item: rows.append(item)
    time.sleep(1.0)

  for vendor, url in VENDOR_URLS:
    item = scrape_generic(url)
    if item:
      item["titre"] = f"[{vendor.upper()}] {item['titre']}"
      rows.append(item)
    time.sleep(1.0)

  df = pd.DataFrame(rows).drop_duplicates(subset=["source","titre","contenu"])
  df = df[df["contenu"].str.len() > 60]
  out_csv = os.path.join(DATA_DIR, "support_dataset_raw.csv")
  out_json = os.path.join(DATA_DIR, "support_dataset_raw.json")
  df.to_csv(out_csv, index=False)
  df.to_json(out_json, orient="records", force_ascii=False, indent=2)
  print(f"✅ Fusion: {len(df)} lignes → {out_csv}")

if __name__ == "__main__":
  run()
