import requests
from bs4 import BeautifulSoup
import pandas as pd

# 🔹 Scraper Microsoft Support
def scrape_microsoft_wifi():
    url = "https://support.microsoft.com/fr-fr/windows/r%C3%A9soudre-les-probl%C3%A8mes-de-connexion-wi-fi-dans-windows-9424a1f7-6a3b-65a6-4d78-7f07eee84d2c"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = []
    for section in soup.select('h2, h3'):
        titre = section.text.strip()
        contenu = section.find_next_sibling('p')
        if contenu:
            data.append({
                'source': 'Microsoft',
                'titre': titre,
                'contenu': contenu.text.strip()
            })
    return data

# 🔹 Scraper Softonic
def scrape_softonic_wifi():
    url = "https://fr.softonic.com/telechargements/pilote-wifi"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = []
    for item in soup.select('.sc-1v6ydtz-0'):
        titre = item.select_one('h3')
        description = item.select_one('p')
        if titre and description:
            data.append({
                'source': 'Softonic',
                'titre': titre.text.strip(),
                'contenu': description.text.strip()
            })
    return data

# 🔹 Scraper 01net
def scrape_01net_wifi():
    url = "https://www.01net.com/telecharger/utilitaire/reseau/wifi-manager.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = []
    titre = soup.select_one('h1')
    description = soup.select_one('.description')
    if titre and description:
        data.append({
            'source': '01net',
            'titre': titre.text.strip(),
            'contenu': description.text.strip()
        })
    return data

# 🔹 Fusion des données
def merge_all_sources():
    all_data = scrape_microsoft_wifi() + scrape_softonic_wifi() + scrape_01net_wifi()
    df = pd.DataFrame(all_data)

    # Export CSV
    df.to_csv('../data/support_wifi_dataset.csv', index=False)

    # Export JSON
    df.to_json('../data/support_wifi_dataset.json', orient='records', force_ascii=False, indent=2)

    print("✅ Données fusionnées et exportées avec succès.")

# 🔹 Exécution
if __name__ == "__main__":
    merge_all_sources()
