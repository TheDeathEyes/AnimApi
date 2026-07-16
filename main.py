from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)
session = requests.Session()
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://anime-sama.to/"
}
BASE_URL = "https://anime-sama.to"

@app.route('/search')
def search():
    query = request.args.get('q', '')
    url = f"{BASE_URL}/catalogue/?search={query}"
    
    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        resultats = []
        
        # LOGIQUE EXACTE DE TON SCRIPT TKINTER
        cards = soup.find_all("div", class_=["cardAnime", "anime-card", "catalog-card"]) 
        if not cards: cards = soup.find_all("a", href=True)
        
        for card in cards:
            if card.name == "div":
                title_el = card.find(["h1", "h2", "h3", "p"]) or card.find(class_=re.compile("title"))
                link_el = card.find("a")
                if title_el and link_el:
                    titre = title_el.text.strip()
                    link = link_el["href"]
                    if link.startswith("/"): link = BASE_URL + link
                    resultats.append({"title": titre, "url": link})
            elif card.name == "a" and "/catalogue/" in card["href"] and card["href"] != "/catalogue/":
                titre = card.text.strip()
                if titre and len(titre) > 1:
                    link = card["href"]
                    if link.startswith("/"): link = BASE_URL + link
                    resultats.append({"title": titre, "url": link})

        # Éviter les doublons
        return jsonify(list({v['title']:v for v in resultats}.values()))
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/debug')
def debug():
    query = request.args.get('q', 'solo')
    url = f"{BASE_URL}/catalogue/?search={query}"
    r = session.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    # On renvoie juste le nombre de div trouvés pour tester si le site répond bien
    return f"Status: {r.status_code} | Nombre de div trouvés: {len(soup.find_all('div'))} | HTML sample: {str(soup.prettify())[:500]}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
