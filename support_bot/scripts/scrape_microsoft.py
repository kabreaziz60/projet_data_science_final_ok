import requests, re, time
from bs4 import BeautifulSoup

HEADERS = {"User-Agent":"Mozilla/5.0"}
URLS = [
  # Wi-Fi
  "https://support.microsoft.com/fr-fr/windows/r%C3%A9soudre-les-probl%C3%A8mes-de-connexion-wi-fi-dans-windows-9424a1f7-6a3b-65a6-4d78-7f07eee84d2c",
  # Mises à jour
  "https://support.microsoft.com/fr-fr/windows/windows-update-faq-16c42daf-2354-8e08-5df9-9d6a3a5b1a45",
  # Imprimantes
  "https://support.microsoft.com/fr-fr/windows/r%C3%A9parer-les-probl%C3%A8mes-d-imprimante-dans-windows-10-ecfe4daf-0b2c-0b7a-4350-76d6f2f7a6f5",
]

def scrape_ms():
  data=[]
  for url in URLS:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("h1")
    # blocs paragraphes et listes
    blocks = soup.select("h2, h3, p, li")
    buf=[]
    for b in blocks:
      t = " ".join(b.get_text(" ", strip=True).split())
      if len(t) >= 40:
        buf.append(t)
    if title and buf:
      data.append({"source": url, "titre": title.get_text(strip=True), "contenu": "\n".join(buf)})
    time.sleep(1.2)
  return data
