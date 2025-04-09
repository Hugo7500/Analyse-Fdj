import os
import zipfile
import logging
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import chardet
from sklearn.cluster import KMeans

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Extraction ZIP ---
def extract_csv_if_zip(file_path):
    if file_path.lower().endswith(".zip"):
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall("extracted_zip")
            for name in zip_ref.namelist():
                if name.endswith(".csv"):
                    return os.path.join("extracted_zip", name)
        raise FileNotFoundError("Aucun fichier CSV trouvé dans le ZIP.")
    return file_path

# --- CONFIGURATION : Encodages possibles pour lecture CSV ---
POSSIBLE_ENCODINGS = ["utf-8", "latin-1", "cp1252"]

def read_csv_with_fallback(file_path, parse_dates=None, dayfirst=True):
    import chardet
    parse_dates = parse_dates or []

    # 🔍 Détection encodage initiale
    with open(file_path, "rb") as f:
        raw_data = f.read(10000)
    detected_encoding = chardet.detect(raw_data)["encoding"]
    if detected_encoding in [None, "ascii"]:
        detected_encoding = "utf-8"

    separators = [";", ",", "\t"]
    encodings = [detected_encoding] + POSSIBLE_ENCODINGS

    # Liste possible de colonnes de dates
    possible_dates = ["date_de_tirage", "Date", "date", "DATE"]
    date_col = None
    df_temp = None

    # 🔁 Première passe : lire sans parse_dates pour détecter la colonne date
    for sep in separators:
        for encoding in encodings:
            try:
                df_temp = pd.read_csv(file_path, sep=sep, encoding=encoding, on_bad_lines="skip")
                df_temp.columns = df_temp.columns.str.strip()
                for col in possible_dates:
                    if col in df_temp.columns:
                        date_col = col
                        break
                if date_col:
                    break
            except Exception:
                continue
        if date_col:
            break

    if not date_col or df_temp is None:
        raise Exception("❌ Aucune colonne de date trouvée dans le fichier.")

    # 🔁 Deuxième passe : lire avec parse_dates
    for sep in separators:
        for encoding in encodings:
            try:
                df = pd.read_csv(
                    file_path,
                    sep=sep,
                    encoding=encoding,
                    parse_dates=[date_col],
                    dayfirst=dayfirst,
                    on_bad_lines="skip"
                )
                df.columns = df.columns.str.strip()
                df = df.rename(columns={date_col: "date_de_tirage"})
                df["date_de_tirage"] = pd.to_datetime(df["date_de_tirage"], format="%d%m%Y", errors="coerce")
                df = df.dropna(subset=["date_de_tirage"])
                return df
            except Exception:
                continue

    raise Exception("❌ Aucun encodage compatible ou séparateur trouvé pour lire le fichier.")

# --- Fréquences et clustering ---
def analyser_frequences(df, boules_cols, chance_col):
    all_boules = df[boules_cols].values.flatten()
    freq_boules = dict(pd.Series(all_boules).value_counts())
    freq_chance = {}
    if chance_col and chance_col in df.columns:
        freq_chance = df[chance_col].value_counts().to_dict()
    return freq_boules, freq_chance

def frequences_par_annee(df, boules_cols, chance_col):
    freq = {}
    df["annee"] = df["date_de_tirage"].dt.year
    for annee, grp in df.groupby("annee"):
        boules = grp[boules_cols].values.flatten()
        freq_b = dict(pd.Series(boules).value_counts())
        freq_c = {}
        if chance_col and chance_col in grp.columns:
            freq_c = dict(pd.Series(grp[chance_col]).value_counts())
        freq[annee] = {"boules": freq_b, "chances": freq_c}
    return freq

def clustering_numeros(freq_boules):
    if not freq_boules:
        return {}
    data = np.array(list(freq_boules.values())).reshape(-1, 1)
    kmeans = KMeans(n_clusters=5, random_state=0, n_init=10).fit(data)
    clusters = {i: [] for i in range(5)}
    for num, label in zip(freq_boules.keys(), kmeans.labels_):
        clusters[label].append(num)
    return clusters

# --- Heatmaps uniquement pour boules ---
def generer_heatmaps(df, boules_cols, chance_col, jeu):
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.colors import LogNorm
    import numpy as np
    import os

    jeu_config = {
        "Loto": 49,
        "Euromillions": 50,
        "Eurodreams": 40,
        "Keno": 70,
        "Amigo": 28,
    }

    taille_max = jeu_config.get(jeu, 50)

    def build_matrix(cols, size):
        mat = np.zeros((size, size), dtype=int)
        for _, row in df[cols].iterrows():
            items = row.values
            for i in range(len(items)):
                for j in range(i + 1, len(items)):
                    if pd.notna(items[i]) and pd.notna(items[j]):
                        try:
                            x = int(items[i]) - 1
                            y = int(items[j]) - 1
                            if 0 <= x < size and 0 <= y < size:
                                mat[x][y] += 1
                                mat[y][x] += 1
                        except ValueError:
                            continue
        return mat

    mat_b = build_matrix(boules_cols, taille_max)

    cmap = "coolwarm"
    os.makedirs("static/heatmaps", exist_ok=True)
    heatmap_boules = f"static/heatmaps/{jeu.lower()}_boules.png"

    # 🔥 Meilleur contraste + suppression annot inutiles
    show_numbers = taille_max <= 30 and np.max(mat_b) < 1000

    plt.figure(figsize=(10, 8))
    sns.heatmap(
        mat_b,
        cmap=cmap,
        xticklabels=range(1, taille_max + 1),
        yticklabels=range(1, taille_max + 1),
        square=True,
        annot=show_numbers,
        fmt="d",
        cbar=True,
        linewidths=0.1,
        linecolor="gray",
        norm=LogNorm(vmin=1, vmax=np.max(mat_b))
    )
    plt.title(f"Heatmap Boules - {jeu}")
    plt.xlabel("Numéros")
    plt.ylabel("Numéros")
    plt.tight_layout()
    plt.savefig(heatmap_boules)
    plt.close()

    return heatmap_boules, ""

# --- Tirages simulés ---
def generer_tirages(freq_boules, freq_chance, nom_jeu, mode="hot"):
    config = {
        "Loto": {"nb_main": 5, "nb_chance": 1},
        "Eurodreams": {"nb_main": 6, "nb_chance": 1},
        "Euromillions": {"nb_main": 5, "nb_chance": 2},
        "Keno": {"nb_main": 10, "nb_chance": 0},
        "Amigo": {"nb_main": 7, "nb_chance": 0},
    }

    jeu_cfg = config.get(nom_jeu, {"nb_main": 5, "nb_chance": 1})
    nb_main = jeu_cfg["nb_main"]
    nb_chance = jeu_cfg["nb_chance"]

    needed_main = max(15, nb_main)
    needed_chances = max(5, nb_chance)

    hot = sorted(freq_boules, key=freq_boules.get, reverse=True)[:needed_main]
    cold = sorted(freq_boules, key=freq_boules.get)[:needed_main]

    top_chances = sorted(freq_chance, key=freq_chance.get, reverse=True)[:needed_chances] if freq_chance else []

    tirages = []
    for _ in range(10):
        if mode == "hot":
            numbers = hot
        elif mode == "cold":
            numbers = cold
        elif mode == "mix":
            # Mélange aléatoire de hot + cold pour chaque tirage
            combined = list(set(hot[:nb_main] + cold[:nb_main]))
            np.random.shuffle(combined)
            numbers = combined
        else:
            return []

        if len(numbers) < nb_main or (nb_chance > 0 and len(top_chances) < nb_chance):
            continue  # skip tirage invalide

        main = sorted(np.random.choice(numbers, nb_main, replace=False).tolist())
        chance = sorted(np.random.choice(top_chances, nb_chance, replace=False).tolist()) if nb_chance > 0 else []
        tirages.append(main + chance)

    return tirages

# --- Rapport final ---
def generer_rapport(df, boules_cols, chance_col,
                    freq_boules, freq_chance,
                    freq_annee, clusters,
                    tirages_hot, tirages_cold, tirages_mix,
                    nom_jeu="Loto"):

    config = {
        "Loto": {"nb_main": 5, "nb_chance": 1, "label_chance": "Chance", "rapport_file": "rapport_loto.txt"},
        "Eurodreams": {"nb_main": 6, "nb_chance": 1, "label_chance": "Numéro Dream", "rapport_file": "rapport_eurodreams.txt"},
        "Euromillions": {"nb_main": 5, "nb_chance": 2, "label_chance": "Étoile", "rapport_file": "rapport_euromillions.txt"},
        "Keno": {"nb_main": 10, "nb_chance": 0, "label_chance": "", "rapport_file": "rapport_keno.txt"},
        "Amigo": {"nb_main": 7, "nb_chance": 0, "label_chance": "", "rapport_file": "rapport_amigo.txt"},
    }

    cfg = config.get(nom_jeu, config["Loto"])
    nb_main = cfg["nb_main"]
    nb_chance = cfg["nb_chance"]
    label_chance = cfg["label_chance"]
    rapport_file = cfg["rapport_file"]

    with open(rapport_file, "w", encoding="utf-8") as f:
        f.write("📊 RAPPORT STATISTIQUE\n")
        f.write(f"Période : {df['date_de_tirage'].min().date()} → {df['date_de_tirage'].max().date()}\n")
        f.write("-" * 60 + "\n\n")

        f.write("🎯 TOP FRÉQUENCES\n")
        for i, (num, count) in enumerate(sorted(freq_boules.items(), key=lambda x: x[1], reverse=True), 1):
            f.write(f"{i}. Numéro {int(num)} → {count} fois\n")

        if freq_chance and nb_chance > 0:
            f.write(f"\n🎲 {label_chance}s :\n")
            for i, (num, count) in enumerate(sorted(freq_chance.items(), key=lambda x: x[1], reverse=True), 1):
                f.write(f"{i}. {label_chance} {int(num)} → {count} fois\n")

        f.write("\n📆 PAR ANNÉE\n")
        for annee, data in freq_annee.items():
            f.write(f"\nAnnée {annee} :\n")
            for j, (num, count) in enumerate(sorted(data["boules"].items(), key=lambda x: x[1], reverse=True), 1):
                f.write(f"{j}. Numéro {int(num)} → {count} fois\n")
            if data["chances"] and nb_chance > 0:
                f.write(f"{label_chance}s :\n")
                for j, (num, count) in enumerate(sorted(data["chances"].items(), key=lambda x: x[1], reverse=True), 1):
                    f.write(f"{j}. {label_chance} {int(num)} → {count} fois\n")

        f.write("\n📊 CLUSTERING\n")
        for i, nums in clusters.items():
            f.write(f"Cluster {i+1} : {', '.join(map(str, sorted(map(int, nums))))}\n")

        f.write("\n🔥 TIRAGES SIMULÉS\n")
        for label, tirages in [("HOT", tirages_hot), ("COLD", tirages_cold), ("MIX", tirages_mix)]:
            f.write(f"\n{label}:\n")
            for t in tirages:
                f.write(f"Main: {t[:nb_main]} | {label_chance}s: {t[nb_main:]}\n" if nb_chance > 0 else f"Main: {t}\n")

    with open(rapport_file, "r", encoding="utf-8") as f:
        return f.read()
    
def analyser_jeu(file_path, jeu, boules_cols, chance_col=None, nb_main=5, nb_chance=1):
    file_path = extract_csv_if_zip(file_path)
    df = read_csv_with_fallback(file_path, parse_dates=["date_de_tirage"], dayfirst=True)
    df = df.dropna(subset=["date_de_tirage"])

    # 🔒 Vérification stricte du jeu en fonction des colonnes présentes
    cols_lower = [c.lower() for c in df.columns]

    if jeu == "Loto":
        if not all(col in cols_lower for col in ["boule_1", "boule_2", "boule_3", "boule_4", "boule_5", "numero_chance"]):
            raise ValueError("❌ Le fichier ne correspond pas au format du jeu Loto.")
    elif jeu == "Eurodreams":
        if not all(col in cols_lower for col in ["boule_1", "boule_2", "boule_3", "boule_4", "boule_5", "boule_6", "numero_dream"]):
            raise ValueError("❌ Le fichier ne correspond pas au format du jeu Eurodreams.")
    elif jeu == "Euromillions":
        if not all(col in cols_lower for col in ["boule_1", "boule_2", "boule_3", "boule_4", "boule_5", "etoile_1", "etoile_2"]):
            raise ValueError("❌ Le fichier ne correspond pas au format du jeu Euromillions.")
    elif jeu == "Keno":
        if not all(col in cols_lower for col in [f"boule{i}" for i in range(1, 21)]):
            raise ValueError("❌ Le fichier ne contient pas les colonnes attendues pour le Keno.")
    elif jeu == "Amigo":
        if not all(col in cols_lower for col in ["n1", "n2", "n3", "n4", "n5", "n6", "n7"]):
            raise ValueError("❌ Le fichier ne correspond pas au format du jeu Amigo.")

    # Traitements
    freq_boules, freq_chance = analyser_frequences(df, boules_cols, chance_col)
    freq_annee = frequences_par_annee(df, boules_cols, chance_col)
    clusters = clustering_numeros(freq_boules)
    heatmap_boules, _ = generer_heatmaps(df, boules_cols, chance_col, jeu)

    tirages_hot = generer_tirages(freq_boules, freq_chance, jeu, "hot")
    tirages_cold = generer_tirages(freq_boules, freq_chance, jeu, "cold")
    tirages_mix = generer_tirages(freq_boules, freq_chance, jeu, "mix")

    rapport = generer_rapport(
        df, boules_cols, chance_col,
        freq_boules, freq_chance,
        freq_annee, clusters,
        tirages_hot, tirages_cold, tirages_mix,
        nom_jeu=jeu
    )

    return {
        "rapport": rapport,
        "heatmap_boules": "/" + heatmap_boules,
        "heatmap_chances": ""  # heatmap chance supprimée
    }