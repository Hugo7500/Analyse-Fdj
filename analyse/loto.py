from analyse.base_analyse import analyser_jeu

# Fonction de génération des tirages optimisés
def generer_tirages(freq_boules, freq_chance, nom_jeu, mode="hot"):
    import numpy as np
    config = {"nb_main": 5, "nb_chance": 1}
    nb_main = config["nb_main"]
    nb_chance = config["nb_chance"]

    needed_main = max(15, nb_main)

    if mode == "hot":
        numbers = sorted(freq_boules, key=freq_boules.get, reverse=True)[:needed_main]
    elif mode == "cold":
        numbers = sorted(freq_boules, key=freq_boules.get)[:needed_main]
    elif mode == "mix":
        hot = sorted(freq_boules, key=freq_boules.get, reverse=True)[:5]
        cold = sorted(freq_boules, key=freq_boules.get)[:5]
        numbers = hot + cold
    else:
        return []

    needed_chances = max(5, nb_chance)
    top_chances = sorted(freq_chance, key=freq_chance.get, reverse=True)[:needed_chances] if freq_chance else []

    if len(numbers) < nb_main or len(top_chances) < nb_chance:
        return []

    tirages = []
    for _ in range(10):
        main = sorted(np.random.choice(numbers, nb_main, replace=False).tolist())
        chance = sorted(np.random.choice(top_chances, nb_chance, replace=False).tolist())
        tirages.append(main + chance)
    return tirages

# Fonction de génération du rapport
def generer_rapport(df, boules_cols, chance_col,
                    freq_boules, freq_chance,
                    freq_annee, clusters,
                    tirages_hot, tirages_cold, tirages_mix,
                    nom_jeu="Loto"):

    nb_main = 5
    nb_chance = 1
    path = "rapport_loto.txt"

    with open(path, "w", encoding="utf-8") as f:
        f.write("📊 RAPPORT STATISTIQUE\n")
        f.write(f"Période : {df['date_de_tirage'].min().date()} → {df['date_de_tirage'].max().date()}\n")
        f.write("-" * 60 + "\n\n")

        f.write("🎯 TOP FRÉQUENCES\n")
        for i, (num, count) in enumerate(sorted(freq_boules.items(), key=lambda x: x[1], reverse=True), 1):
            f.write(f"{i}. Numéro {int(num)} → {count} fois\n")

        if freq_chance:
            f.write("\n🎲 Numéros Chance :\n")
            for i, (num, count) in enumerate(sorted(freq_chance.items(), key=lambda x: x[1], reverse=True), 1):
                f.write(f"{i}. Chance {int(num)} → {count} fois\n")

        f.write("\n📆 PAR ANNÉE\n")
        for annee, data in freq_annee.items():
            f.write(f"\nAnnée {annee} :\n")
            for j, (num, count) in enumerate(sorted(data["boules"].items(), key=lambda x: x[1], reverse=True), 1):
                f.write(f"{j}. Numéro {int(num)} → {count} fois\n")

        f.write("\n📊 CLUSTERING\n")
        for i, nums in clusters.items():
            f.write(f"Cluster {i+1} : {', '.join(map(str, sorted(map(int, nums))))}\n")

        f.write("\n🔥 TIRAGES SIMULÉS\n")
        for label, tirages in [("HOT", tirages_hot), ("COLD", tirages_cold), ("MIX", tirages_mix)]:
            f.write(f"\n{label}:\n")
            for t in tirages:
                f.write(f"Main: {t[:nb_main]} | Chance: {t[nb_main:]}\n")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# Fonction appelée par app.py
def loto(file_path):
    return analyser_jeu(
        file_path,
        jeu="Loto",
        boules_cols=["boule_1", "boule_2", "boule_3", "boule_4", "boule_5"],
        chance_col="numero_chance",
        nb_main=5,
        nb_chance=1
    )