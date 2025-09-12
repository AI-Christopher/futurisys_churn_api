"""
Préprocessing des données pour l'API Futurisys Churn.

Ce module regroupe les fonctions utilisées par l’endpoint /predict pour :
- nettoyer les noms de colonnes,
- convertir des binaires textuels en entiers (0/1),
- créer des variables dérivées (feature engineering),
- encoder les variables catégorielles (one-hot + encodage ordinal).

⚠️ Important : ce module ne change pas le contrat avec le modèle.
Les fonctions et leurs effets restent identiques à la version validée par les tests.
"""

import re
import pandas as pd
from .constants import (
    MOYENNES_POSTE,   # moyenne des salaires par poste (pour ratio_revenu_poste)
    MAPPING_POSTE,    # encodage ordinal du poste
    MAPPING_FREQ,     # encodage ordinal de la fréquence de déplacement
)

def clean_col_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie les noms de colonnes en supprimant les caractères spéciaux.

    Règle : ne garder que [A-Za-z0-9_] dans les noms, afin d'éviter des surprises
    lors des get_dummies / reindex et d’être compatible avec les features du modèle.

    Paramètres
    ----------
    df : pd.DataFrame
        Jeu de données à modifier (les noms de colonnes seront réécrits).

    Retour
    ------
    pd.DataFrame
        Le même DataFrame, avec ses colonnes nettoyées (effet en place).
    """
    cols = df.columns
    new_cols = []
    for col in cols:
        new_col = re.sub(r'[^A-Za-z0-9_]+', '', col)
        new_cols.append(new_col)
    df.columns = new_cols
    return df


def convert_binary_to_int(df: pd.DataFrame, col_name: str, positive_value: str = "Oui")-> pd.DataFrame:
    """
    Convertit une colonne binaire textuelle en entiers 0/1.

    - Si la colonne est de type object, on remplace `positive_value` par 1 et tout le reste par 0.
    - Si la colonne n'existe pas, on ne lève pas d'erreur (on loggue via print et on renvoie df inchangé).

    Paramètres
    ----------
    df : pd.DataFrame
        Données d'entrée.
    col_name : str
        Nom de la colonne binaire à convertir (ex: 'heure_supplementaires', 'genre').
    positive_value : str, défaut "Oui"
        Valeur considérée comme positive (1). Les autres deviennent 0.

    Retour
    ------
    pd.DataFrame
        Le DataFrame (colonne convertie si présente).
    """
    if col_name in df.columns:
        # Si la colonne est textuelle, on la mappe vers 0/1 puis on caste en int
        if df[col_name].dtype == "object":
            df[col_name] = df[col_name].apply(lambda x: 1 if x == positive_value else 0)
            df[col_name] = df[col_name].astype(int)
    else:
        # Choix de design : ne pas lever d’erreur pour garder un flux robuste côté API.
        # (On pourrait passer à un logger si besoin.)
        print(f"Colonne {col_name} n'existe pas dans le DataFrame.")
    return df

def add_features(df: pd.DataFrame)-> pd.DataFrame:
    """
    Crée des variables dérivées utilisées par le modèle (feature engineering).

    Variables créées
    ----------------
    - ratio_revenu_poste : revenu_mensuel / (moyenne du poste + 1)
    - ratio_augmentation_promotion : augementation_salaire_precedente / (annees_depuis_la_derniere_promotion + 1)

    Contraintes
    -----------
    - Les colonnes suivantes doivent être présentes :
      {'revenu_mensuel', 'poste', 'augementation_salaire_precedente', 'annees_depuis_la_derniere_promotion'}

    Lève
    ----
    ValueError
        Si une ou plusieurs colonnes requises sont absentes.

    Retour
    ------
    pd.DataFrame
        Une copie du DataFrame, avec les colonnes dérivées ajoutées.
    """
    df = df.copy()

    required = {
        "revenu_mensuel", 
        "poste",
        "augementation_salaire_precedente", 
        "annees_depuis_la_derniere_promotion"
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes pour add_features: {sorted(missing)}")
    
   # Ratio revenu vs moyenne du poste (le +1 évite la division par 0 en cas de poste inconnu)
    revenu_moyen_par_poste = df["poste"].map(MOYENNES_POSTE)
    df["ratio_revenu_poste"] = (df["revenu_mensuel"] / (revenu_moyen_par_poste + 1)).fillna(1.0)
    
    # Ratio augmentation / années depuis promo (+1 pour éviter /0)
    df["ratio_augmentation_promotion"] = (
        df["augementation_salaire_precedente"] / 
        (df["annees_depuis_la_derniere_promotion"] + 1)
    )

    return df


def encode_categorical(df: pd.DataFrame)-> pd.DataFrame:
    """
    Encode les variables catégorielles :
    - One-Hot Encoding pour ['statut_marital', 'domaine_etude', 'departement'] via pandas.get_dummies.
    - Nettoyage des noms de colonnes (sécurité).
    - Encodage ordinal pour 'poste' (MAPPING_POSTE) et 'frequence_deplacement' (MAPPING_FREQ).

    ⚠️ Le mapping ordinal suppose que les valeurs source existent dans MAPPING_POSTE / MAPPING_FREQ.
       Sinon, les valeurs seront NaN, ce qui sera ensuite comblé par reindex côté API.

    Paramètres
    ----------
    df : pd.DataFrame
        Données d'entrée.

    Retour
    ------
    pd.DataFrame
        Une copie encodée (one-hot + ordinal) et aux colonnes nettoyées.
    """
    df = df.copy()

    # One-Hot (sans colonne NaN) sur ces variables
    categorical_cols_to_encode = ['statut_marital', 'domaine_etude', 'departement']
    df = pd.get_dummies(df, columns=categorical_cols_to_encode, dummy_na=False)

    # Nettoyage des noms de colonnes pour garantir la compatibilité modèle
    df = clean_col_names(df)

    # Encodage ordinal (valeurs non mappées -> NaN)
    df['poste'] = df['poste'].map(MAPPING_POSTE)
    df['frequence_deplacement'] = df['frequence_deplacement'].map(MAPPING_FREQ)

    return df