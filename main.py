from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)
session = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

@app.route('/search')
def search():
    query = request.args.get('q', '')
    r = session.get(f"https://anime-sama.to/catalogue/?search={query}", headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for a in soup.find_all("a", href=True):
        if "/catalogue/" in a['href'] and len(a.text.strip()) > 3:
            # On nettoie l'URL
            link = a['href']
            if not link.startswith("http"): link = "https://anime-sama.to" + link
            results.append({"title": a.text.strip(), "url": link})
    return jsonify(list({v['title']:v for v in results}.values()))

@app.route('/episodes')
def episodes():
    url = request.args.get('url', '').rstrip('/')
    # On cherche le fichier episodes.js comme dans ton logiciel
    # On teste les chemins les plus probables
    paths = ["/vostfr/episodes.js", "/vf/episodes.js", "/episodes.js"]
    for path in paths:
        js_url = f"{url}{path}"
        r = session.get(js_url, headers=HEADERS)
        if r.status_code == 200 and "eps" in r.text:
            # Extraction des liens via regex (la même logique que ton Tkinter)
            blocs = re.findall(r"var\s+(eps\d+)\s*=\s*\[([\s\S]*?)\]", r.text)
            final_eps = []
            for nom_var, bloc_liens in blocs:
                liens = re.findall(r"['\"](https?://[^\s'\"`><]+)['\"]", bloc_liens)
                if liens:
                    final_eps.append({"title": f"Lecteur {nom_var.replace('eps','')}", "link": liens[0]})
            return jsonify(final_eps)
    return jsonify([]) # Vide si rien trouvé

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
