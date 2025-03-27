from analyse.base_analyse import analyser_jeu

def keno(file_path):
    return analyser_jeu(
        file_path,
        jeu="Keno",
        boules_cols=[f"boule{i}" for i in range(1, 21)],  # ✅ UNE COLONNE PAR BOULE
        chance_col=None,
        nb_main=10,
        nb_chance=0
    )