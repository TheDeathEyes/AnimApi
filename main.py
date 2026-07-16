from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import os

app = Flask(__name__)
CORS(app) # Crucial pour que ton index.php puisse appeler Render sans blocage

BASE_URL = "https://anime-sama.to"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://anime-sama.to/"
}

@app.route('/search')
def search():
    query = request.args.get('q', '')
    try:
        r = requests.get(f"{BASE_URL}/api/search.php?q={query}", headers=HEADERS, timeout=7)
        return r.text, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify([])

@app.route('/details')
def details():
    anime_url = request.args.get('url', '').rstrip('/')
    try:
        r = requests.get(anime_url, headers=HEADERS, timeout=7)
        page_html = r.text
    except:
        return jsonify({"synopsis": "", "versions": {}})

    synopsis = "Aucun synopsis disponible."
    m_syn = re.search(r'<p id="synopsisText"[^>]*>([\s\S]*?)</p>', page_html, re.IGNORECASE)
    if m_syn:
        synopsis = re.sub('<[^<]+?>', '', m_syn.group(1)).strip()

    variantes = ["/vostfr/episodes.js", "/vf/episodes.js", "/saison1/vostfr/episodes.js", "/saison1/vf/episodes.js", "/episodes.js"]
    donnees_versions = {}

    for sous_url in variantes:
        try:
            js_res = requests.get(anime_url + sous_url, headers=HEADERS, timeout=4)
            js_content = js_res.text
        except:
            continue

        if "eps" in js_content:
            nom_version = sous_url.replace("/episodes.js", "").strip("/").upper()
            if not nom_version: nom_version = "PRINCIPALE"
            
            if nom_version not in donnees_versions:
                donnees_versions[nom_version] = {}

            matches = re.findall(r'var\s+(eps\d+)\s*=\s*\[([\s\S]*?)\]', js_content)
            for var_name, content_array in matches:
                liens = re.findall(r'[\'"](https?://[^\s\'"`><]+)[\'"]', content_array)
                if liens:
                    liens_corriges = [l.replace('vidmoly.to', 'vidmoly.biz') for l in liens]
                    num_lecteur = var_name.replace('eps', '')
                    
                    premier = liens_corriges[0].lower()
                    if 'vidmoly' in premier: nom_hebergeur = f"⭐ Vidmoly (Lecteur {num_lecteur})"
                    elif 'sibnet' in premier: nom_hebergeur = f"🚀 Sibnet (Lecteur {num_lecteur})"
                    else: nom_hebergeur = f"Lecteur {num_lecteur}"

                    donnees_versions[nom_version][nom_hebergeur] = liens_corriges

            donnees_versions[nom_version] = dict(sorted(
                donnees_versions[nom_version].items(),
                key=lambda item: 0 if "Vidmoly" in item[0] else (1 if "Sibnet" in item[0] else 2)
            ))

    return jsonify({"synopsis": synopsis, "versions": donnees_versions})

if __name__ == '__main__':
    # Configuration requise pour l'hébergement en ligne
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
