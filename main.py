from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Configuration globale
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://anime-sama.to/"
}
BASE_URL = "https://anime-sama.to"
session = requests.Session()

# 1. Route pour rechercher les animes
@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query: return jsonify([])
    
    url = f"{BASE_URL}/catalogue/?search={query}"
    try:
        response = session.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        resultats = []
        
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

        return jsonify(list({v['title']:v for v in resultats}.values()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Route pour extraire Métadonnées + Episodes
@app.route('/episodes')
def get_episodes():
    url_anime = request.args.get('url')
    if not url_anime:
        return jsonify({"error": "URL manquante"}), 400

    # --- PARTIE 1 : EXTRACTION METADONNEES ---
    metadata = {"synopsis": "Synopsis non disponible.", "image": "", "trailer": None}
    try:
        page_res = session.get(url_anime, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(page_res.text, "html.parser")
        
        # Synopsis
        synopsis_p = soup.find("p", id="synopsisText") or soup.find("p", class_=["synopsis", "text-sm"])
        if synopsis_p: metadata["synopsis"] = synopsis_p.text.strip()
        
        # Image
        img_tag = soup.find("meta", property="og:image") or soup.find("img", class_="cover")
        if img_tag: metadata["image"] = img_tag.get("content") or img_tag.get("src")
        
        # Trailer
        trailer_iframe = soup.find("iframe", src=re.compile(r"youtube|dailymotion|vimeo"))
        if trailer_iframe: metadata["trailer"] = trailer_iframe.get("src")
    except:
        pass

    # --- PARTIE 2 : EXTRACTION EPISODES ---
    url_base = url_anime.rstrip('/')
    donnees_episodes = {}
    
    variantes_sous_urls = [
        f"{url_base}/vostfr/episodes.js",
        f"{url_base}/vf/episodes.js",
        f"{url_base}/saison1/vostfr/episodes.js",
        f"{url_base}/saison1/vf/episodes.js",
        f"{url_base}/episodes.js"
    ]

    for js_url in variantes_sous_urls:
        try:
            js_res = session.get(js_url, headers=HEADERS, timeout=5)
            if js_res.status_code == 200 and "eps" in js_res.text:
                nom_version = js_url.replace(url_base, "").replace("/episodes.js", "").strip("/").upper()
                if not nom_version: nom_version = "PRINCIPALE"

                if nom_version not in donnees_episodes:
                    donnees_episodes[nom_version] = {}

                blocs = re.findall(r"var\s+(eps\d+)\s*=\s*\[([\s\S]*?)\]", js_res.text)
                
                for nom_var, bloc_liens in blocs:
                    liens_bruts = re.findall(r"['\"](https?://[^\s'\"`><]+)['\"]", bloc_liens)
                    if liens_bruts:
                        num_lecteur = nom_var.replace("eps", "")
                        nom_hebergeur = f"Lecteur {num_lecteur}"
                        
                        liens_corriges = []
                        for l in liens_bruts:
                            if "vidmoly.to" in l.lower(): l = l.replace("vidmoly.to", "vidmoly.biz")
                            liens_corriges.append(l)

                        # Typage du lecteur
                        premier_lien = liens_corriges[0].lower()
                        if "embed4me" in premier_lien: nom_hebergeur += " (Embed4me)"
                        elif "vidmoly" in premier_lien: nom_hebergeur += " (Vidmoly)"
                        elif "sibnet" in premier_lien: nom_hebergeur += " (Sibnet)"
                        elif "uqload" in premier_lien: nom_hebergeur += " (Uqload)"
                        elif "sendvid" in premier_lien: nom_hebergeur += " (Sendvid)"
                        elif "streamtape" in premier_lien: nom_hebergeur += " (Streamtape)"
                        
                        donnees_episodes[nom_version][nom_hebergeur] = {
                            "num": num_lecteur,
                            "liens": liens_corriges
                        }
        except:
            continue

    return jsonify({"metadata": metadata, "episodes": donnees_episodes})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
