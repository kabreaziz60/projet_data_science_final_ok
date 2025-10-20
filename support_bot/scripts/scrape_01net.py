import requests
from bs4 import BeautifulSoup
def scrape_01net_wifi():
    url = "https://www.01net.com/telecharger/utilitaire/reseau/wifi-manager.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = []
    titre = soup.select_one('h1')
    description = soup.select_one('.description')
    if titre and description:
        data.append({'source': '01net', 'titre': titre.text.strip(), 'contenu': description.text.strip()})
    return data
