import pandas as pd
import chardet

POSSIBLE_ENCODINGS = ["utf-8", "latin-1", "cp1252"]

def read_csv_with_fallback(file_path, parse_dates=None, dayfirst=True):
    parse_dates = parse_dates or []

    # 🔍 Détection encodage initiale
    with open(file_path, "rb") as f:
        raw_data = f.read(10000)
    detected_encoding = chardet.detect(raw_data)["encoding"]

    if detected_encoding in [None, "ascii"]:
        detected_encoding = "utf-8"

    separators = [";", ",", "\t"]
    encodings = [detected_encoding] + POSSIBLE_ENCODINGS

    possible_dates = ["date_de_tirage", "Date", "date", "DATE"]
    date_col = None

    # Première passe sans parse_dates pour détecter les colonnes
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

    if not date_col:
        raise Exception("❌ Aucune colonne de date trouvée dans le fichier.")

    # Lecture finale avec parse_dates
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
                df["date_de_tirage"] = pd.to_datetime(df["date_de_tirage"], errors="coerce", dayfirst=dayfirst)
                return df
            except Exception:
                continue

    raise Exception("❌ Aucun encodage compatible ou séparateur trouvé pour lire le fichier.")

# 🔎 TEST SUR FICHIER AMIGO
if __name__ == "__main__":
    file_path = "amigo_202201.csv"  # ou "./uploads/amigo_202201.csv" si nécessaire
    df = read_csv_with_fallback(file_path)
    print("\n✅ Lecture réussie")
    print("Colonnes :", df.columns.tolist())
    print("Premières dates :")
    print(df["date_de_tirage"].head())