import re
import pandas as pd
from .constants import (
    MOYENNES_POSTE,
    MAPPING_POSTE,
    MAPPING_FREQ
)

def clean_col_names(df)-> pd.DataFrame:
    cols = df.columns
    new_cols = []
    for col in cols:
        new_col = re.sub(r'[^A-Za-z0-9_]+', '', col)
        new_cols.append(new_col)
    df.columns = new_cols
    return df

def convert_binary_to_int(df, col_name, positive_value="Oui")-> pd.DataFrame:
    if col_name in df.columns:
        # Convertit les valeurs de la colonne en int
        if df[col_name].dtype == 'object':
            # Si la colonne est de type object, on applique la conversion
            df[col_name] = df[col_name].apply(lambda x: 1 if x == positive_value else 0)

            # Convertit les valeurs de la colonne en int
            df[col_name] = df[col_name].astype(int)
    else:
        print(f"Colonne {col_name} n'existe pas dans le DataFrame.")
    
    return df

def add_features(df: pd.DataFrame)-> pd.DataFrame:
    
    # (optionnel) garde une copie pour ne pas modifier l’entrée
    df = df.copy()

    # Vérifie la présence des colonnes nécessaires (facilite le debug)
    required = {
        "revenu_mensuel", "poste",
        "augementation_salaire_precedente", "annees_depuis_la_derniere_promotion"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes pour add_features: {sorted(missing)}")
    
    # Ratio revenu vs moyenne du poste
    revenu_moyen_par_poste = df["poste"].map(MOYENNES_POSTE)
    df["ratio_revenu_poste"] = (df["revenu_mensuel"] / (revenu_moyen_par_poste + 1)).fillna(1.0)
    
    # Ratio augmentation / années depuis promo (+1 pour éviter /0)
    df["ratio_augmentation_promotion"] = (df["augementation_salaire_precedente"] / (df["annees_depuis_la_derniere_promotion"] + 1))

    return df


def encode_categorical(df: pd.DataFrame)-> pd.DataFrame:
    # (optionnel) garde une copie pour ne pas modifier l’entrée
    df = df.copy()

    # Variables catégorielles (One-Hot Encoding)
    categorical_cols_to_encode = ['statut_marital', 'domaine_etude', 'departement']
    df = pd.get_dummies(df, columns=categorical_cols_to_encode, dummy_na=False)

    # Nettoyage des noms de colonnes (supprime les caractères spéciaux)
    df = clean_col_names(df)

    # Encodage Ordinal
    df['poste'] = df['poste'].map(MAPPING_POSTE)
    df['frequence_deplacement'] = df['frequence_deplacement'].map(MAPPING_FREQ)

    return df