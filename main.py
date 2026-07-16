from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)
session = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}

@app.route('/search')
def search():
    query = request.args.get('q', '')
    r = session.get(f"https://anime-sama.to/catalogue/?search={query}", headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for a in soup.find_all("a", href=True):
        if "/catalogue/" in a['href'] and len(a.text.strip()) > 3:
            results.append({"title": a.text.strip(), "url": "https://anime-sama.to" + a['href']})
    return jsonify(list({v['title']:v for v in results}.values()))

@app.route('/episodes')
def episodes():
    url = request.args.get('url', '')
    r = session.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    # On récupère tous les liens qui semblent être des épisodes
    eps = [{"title": a.text.strip(), "link": "https://anime-sama.to" + a['href']} 
           for a in soup.select("a.btn-episode")] # Vérifie la classe sur le site
    return jsonify(eps)

@app.route('/player')
def player():
    url = request.args.get('url', '')
    r = session.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    # Récupère l'iframe du lecteur
    iframe = soup.find("iframe", src=True)
    return jsonify({"player_url": iframe['src'] if iframe else ""})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
