import requests, time
from bs4 import BeautifulSoup

HEADERS={"User-Agent":"Mozilla/5.0"}
VENDOR_URLS = [
  ("lenovo","https://support.lenovo.com/fr/fr/solutions/ht502846-windows-10-wifi-troubleshooting"),
  ("hp","https://support.hp.com/fr-fr/help/diagnostics/wireless-network-and-internet"),
  ("dell","https://www.dell.com/support/kbdoc/fr-fr/000124630/windows-10-r%C3%A9solution-des-probl%C3%A8mes-de-r%C3%A9seau-sans-fil"),
  ("mozilla","https://support.mozilla.org/fr/kb/resoudre-les-problemes-de-connexion"),
  ("ubuntu","https://help.ubuntu.com/stable/ubuntu-help/net-wireless-troubleshooting.html.fr") # si FR dispo
]

def scrape_vendor_docs():
  rows=[]
  for vendor, url in VENDOR_URLS:
    try:
      r=requests.get(url, headers=HEADERS, timeout=20)
      r.raise_for_status()
      soup=BeautifulSoup(r.text,"html.parser")
      title=soup.find(["h1","h2"])
      parts = soup.select("h2, h3, p, li")
      buf=[]
      for p in parts:
        tx=p.get_text(" ", strip=True)
        if len(tx) >= 50:
          buf.append(tx)
      if title and buf:
        rows.append({"source": url, "titre": f"[{vendor.upper()}] {title.get_text(strip=True)}", "contenu":"\n".join(buf)})
      time.sleep(1.0)
    except Exception:
      continue
  return rows
