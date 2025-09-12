# tests/test_encode_categorical.py
"""
But du fichier
--------------
Valider le comportement de la fonction `encode_categorical` :
1) création de dummies (one-hot) pour certaines colonnes catégorielles,
2) encodage ordinal pour `poste` et `frequence_deplacement`,
3) non-mutation du DataFrame d’entrée,
4) types numériques pour les colonnes encodées,
5) gestion des valeurs inconnues (→ NaN).

Contexte
--------
- `clean_col_names` supprime les caractères spéciaux dans les noms de colonnes,
  donc on l’utilise pour prédire les noms de dummies finaux.
- Les mappings attendus sont fournis par `MAPPING_POSTE` et `MAPPING_FREQ`.
"""

import pandas as pd
import numpy as np
from futurisys_churn_api.api.preprocessing import (
    encode_categorical, clean_col_names, MAPPING_POSTE, MAPPING_FREQ
)


def _expected_dummy_names(prefix: str, values: list[str]) -> list[str]:
    """
    Construit les noms de colonnes de dummies attendues après normalisation
    des noms via `clean_col_names`. Utile pour comparer les colonnes générées.

    Exemple :
        prefix="statut_marital", values=["Célibataire", "Marié(e)"]
        -> ["statut_marital_Celibataire", "statut_marital_Mariee"]
    """
    raw = [f"{prefix}_{v}" for v in values]
    df_cols = pd.DataFrame(columns=raw)
    return list(clean_col_names(df_cols).columns)


def test_encode_categorical_basic():
    """
    Cas nominal :
    - dummies créées pour `statut_marital`, `domaine_etude`, `departement`,
    - encodage ordinal pour `poste` et `frequence_deplacement`,
    - le DataFrame d’entrée n’est pas modifié (no in-place mutation),
    - types numériques pour les colonnes encodées.
    """
    df_in = pd.DataFrame({
        "statut_marital": ["Célibataire", "Marié(e)"],
        "domaine_etude": ["Infra & Cloud", "Marketing"],
        "departement": ["Ressources Humaines", "Commercial"],
        "poste": ["Manager", "Consultant"],
        "frequence_deplacement": ["Fréquent", "Occasionnel"],
    })
    df_orig = df_in.copy(deep=True)  # référence pour vérifier la non-mutation

    out = encode_categorical(df_in)

    # 1) vérifier qu'on ne modifie pas df_in (pas d'effet de bord)
    pd.testing.assert_frame_equal(df_in, df_orig)

    # 2) les colonnes brutes catégorielles ont disparu (remplacées par dummies)
    for col in ["statut_marital", "domaine_etude", "departement"]:
        assert col not in out.columns

    # 3) vérifier la présence des dummies attendues
    expected_statut = _expected_dummy_names("statut_marital", ["Célibataire", "Marié(e)"])
    expected_dom    = _expected_dummy_names("domaine_etude", ["Infra & Cloud", "Marketing"])
    expected_dept   = _expected_dummy_names("departement", ["Ressources Humaines", "Commercial"])
    for c in expected_statut + expected_dom + expected_dept:
        assert c in out.columns

    # 4) vérifier l'encodage ordinal
    assert out.loc[0, "poste"] == MAPPING_POSTE["Manager"]
    assert out.loc[1, "poste"] == MAPPING_POSTE["Consultant"]
    assert out.loc[0, "frequence_deplacement"] == MAPPING_FREQ["Fréquent"]
    assert out.loc[1, "frequence_deplacement"] == MAPPING_FREQ["Occasionnel"]

    # 5) vérifier le type numérique des colonnes encodées
    assert np.issubdtype(out["poste"].dtype, np.number)
    assert np.issubdtype(out["frequence_deplacement"].dtype, np.number)


def test_encode_categorical_unknown_values_become_nan():
    """
    Valeurs inconnues pour `poste` et `frequence_deplacement` :
    l’encodage ordinal renvoie NaN (au lieu d’une valeur arbitraire).
    """
    df = pd.DataFrame({
        "statut_marital": ["Célibataire"],
        "domaine_etude": ["Marketing"],
        "departement": ["Commercial"],
        "poste": ["Inconnu"],                 # hors mapping
        "frequence_deplacement": ["Bizarre"], # hors mapping
    })
    out = encode_categorical(df)

    # Les valeurs non mappées doivent devenir NaN
    assert pd.isna(out.loc[0, "poste"])
    assert pd.isna(out.loc[0, "frequence_deplacement"])
