from analyse.base_analyse import analyser_jeu

def amigo(file_path):
    return analyser_jeu(
        file_path,
        jeu="Amigo",
        boules_cols=["N1", "N2", "N3", "N4", "N5", "N6", "N7"],
        chance_col=None,
        nb_main=7,
        nb_chance=0
    )