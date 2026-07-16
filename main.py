from flask import Flask, request, jsonify
from flask_cors import CORS
import requests, re
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)
session = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# 1. Fonction pour extraire les lecteurs d'une URL de saison/langue précise
def extraire_lecteurs(url_saison):
    r = session.get(url_saison, headers=HEADERS)
    if r.status_code != 200: return []
    
    # On cherche le fichier episodes.js dans cette page
    soup = BeautifulSoup(r.text, "html.parser")
    # Parfois le lien vers le JS est dans un script src
    scripts = soup.find_all("script", src=True)
    for s in scripts:
        if "episodes.js" in s['src']:
            js_url = s['src'] if s['src'].startswith("http") else url_saison.rstrip('/') + "/" + s['src'].lstrip('/')
            js_r = session.get(js_url, headers=HEADERS)
            if "eps" in js_r.text:
                blocs = re.findall(r"var\s+(eps\d+)\s*=\s*\[([\s\S]*?)\]", js_r.text)
                eps = []
                for nom_var, bloc in blocs:
                    liens = re.findall(r"['\"](https?://[^\s'\"`><]+)['\"]", bloc)
                    if liens: eps.append({"title": f"Lecteur {nom_var.replace('eps','')}", "link": liens[0]})
                return eps
    return []

@app.route('/episodes')
def episodes():
    url_base = request.args.get('url', '').rstrip('/')
    
    # Étape 1 : On récupère tous les liens qui ressemblent à des saisons/langues
    r = session.get(url_base, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # On cherche les liens contenant /vostfr/ ou /vf/ ou /saison/
    liens_saisons = []
    for a in soup.find_all("a", href=True):
        if any(x in a['href'] for x in ["/vostfr/", "/vf/", "/saison"]):
            full_link = a['href'] if a['href'].startswith("http") else "https://anime-sama.to" + a['href']
            liens_saisons.append(full_link)
    
    # On supprime les doublons
    liens_saisons = list(set(liens_saisons))
    
    # Étape 2 : On explore ces liens pour trouver les lecteurs
    tous_les_lecteurs = []
    for lien in liens_saisons:
        tous_les_lecteurs.extend(extraire_lecteurs(lien))
        
    return jsonify(tous_les_lecteurs)
