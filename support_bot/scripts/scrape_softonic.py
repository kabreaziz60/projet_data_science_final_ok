import requests
from bs4 import BeautifulSoup

def scrape_softonic_wifi():
    #url = "https://fr.softonic.com/telechargements/pilote-wifi"
    url = "https://support.microsoft.com/fr-fr"

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = []
    for item in soup.select('.sc-1v6ydtz-0'):
        titre = item.select_one('h3')
        description = item.select_one('p')
        if titre and description:
            data.append({'source': 'Softonic', 'titre': titre.text.strip(), 'contenu': description.text.strip()})
    return data
