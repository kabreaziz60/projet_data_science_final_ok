import requests
from bs4 import BeautifulSoup


def scrape_microsoft_wifi():
    url = "https://support.microsoft.com/fr-fr/windows/r%C3%A9soudre-les-probl%C3%A8mes-de-connexion-wi-fi-dans-windows-9424a1f7-6a3b-65a6-4d78-7f07eee84d2c"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = []
    for section in soup.select('h2, h3'):
        titre = section.text.strip()
        contenu = section.find_next_sibling('p')
        if contenu:
            data.append({'source': 'Microsoft', 'titre': titre, 'contenu': contenu.text.strip()})
    return data
