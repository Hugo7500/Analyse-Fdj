import os
import tempfile
import logging
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

# Imports des fonctions d’analyse depuis chaque module
from analyse.loto import loto
from analyse.euromillions import euromillions
from analyse.eurodreams import eurodreams
from analyse.keno import keno
from analyse.amigo import amigo

# Dossiers
UPLOAD_FOLDER = "uploads"
LOG_FOLDER = "logs"
RAPPORT_FOLDER = "rapports"
EXTRACT_FOLDER = "extracted_zip"

# Création des dossiers si besoin
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(RAPPORT_FOLDER, exist_ok=True)
os.makedirs(EXTRACT_FOLDER, exist_ok=True)

# Configuration des logs
logging.basicConfig(
    filename=os.path.join(LOG_FOLDER, "loto_analysis.log"),
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialisation de Flask
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Dictionnaire des jeux disponibles
ANALYSEURS = {
    "Loto": loto,
    "Euromillions": euromillions,
    "Eurodreams": eurodreams,
    "Keno": keno,
    "Amigo": amigo,
}

# Page d’accueil
@app.route("/")
def index():
    return render_template("index.html")

# Upload et traitement du fichier
@app.route("/upload", methods=["POST"])
def upload():
    if "csv" not in request.files or "jeu" not in request.form:
        return jsonify({"success": False, "message": "Fichier ou jeu manquant."})

    fichier = request.files["csv"]
    nom_jeu = request.form["jeu"]

    if fichier.filename == "":
        return jsonify({"success": False, "message": "Aucun fichier sélectionné."})

    if nom_jeu not in ANALYSEURS:
        return jsonify({"success": False, "message": f"Jeu inconnu : {nom_jeu}"})

    try:
        # Sauvegarde temporaire du fichier
        filename = secure_filename(fichier.filename)
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        fichier.save(temp_path)
        logger.info(f"Fichier reçu : {filename}")

        # Appel dynamique de la bonne fonction d’analyse
        analyse_fonction = ANALYSEURS[nom_jeu]
        result = analyse_fonction(temp_path)

        return jsonify({
            "success": True,
            "rapport": result.get("rapport", ""),
            "heatmap_boules": result.get("heatmap_boules", ""),
            "heatmap_chances": result.get("heatmap_chances", "")  # peut être vide
        })

    except Exception as e:
        logger.exception("Erreur lors de l’analyse du fichier.")
        return jsonify({"success": False, "message": str(e)})

# Démarrage du serveur Flask
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)