from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)
session = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

@app.route('/search')
def search():
    query = request.args.get('q', '')
    url = f"https://anime-sama.to/catalogue/?search={query}"
    r = session.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    res = []
    # Logique de scraping de ton Tkinter
    cards = soup.find_all("a", href=re.compile(r"/catalogue/"))
    for card in cards:
        if card.text.strip():
            res.append({"title": card.text.strip(), "url": card["href"] if card["href"].startswith("http") else "https://anime-sama.to"+card["href"]})
    return jsonify(list({v['title']:v for v in res}.values()))

@app.route('/details')
def details():
    url = request.args.get('url', '')
    r = session.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # 1. Synopsis
    syno = soup.find("p", id="synopsisText")
    syno_text = syno.text.strip() if syno else "Pas de synopsis."

    # 2. Recherche fichiers JS (ta logique de variantes)
    donnees = {}
    variantes = ["/vostfr/", "/vf/", "/saison1/vostfr/", "/saison1/vf/", "/"]
    
    for v in variantes:
        target = (url.rstrip('/') + v + "episodes.js").replace("//episodes", "/episodes")
        js_r = session.get(target, headers=HEADERS)
        
        if js_r.status_code == 200 and "eps" in js_r.text:
            nom_v = v.strip('/').upper() or "PRINCIPALE"
            donnees[nom_v] = {}
            blocs = re.findall(r"var\s+(eps\d+)\s*=\s*\[([\s\S]*?)\]", js_r.text)
            
            for nom_var, bloc in blocs:
                liens = re.findall(r"['\"](https?://[^\s'\"`><]+)['\"]", bloc)
                if liens:
                    # Correction vidmoly
                    liens = [l.replace("vidmoly.to", "vidmoly.biz") for l in liens]
                    donnees[nom_v][f"Lecteur {nom_var.replace('eps','')}"] = liens
                    
    return jsonify({"synopsis": syno_text, "lecteurs": donnees})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
