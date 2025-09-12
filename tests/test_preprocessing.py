
"""
Tests unitaires du module de prétraitement (preprocessing).

Objectifs
---------
- Vérifier le nettoyage des noms de colonnes (suppression des espaces, accents, caractères spéciaux).
- Vérifier la conversion binaire -> entier pour des colonnes de type "Oui/Non".
- Vérifier l'ajout de variables dérivées (features engineering) et leurs valeurs.
"""

import pandas as pd
from futurisys_churn_api.api.preprocessing import (
    clean_col_names,
    convert_binary_to_int,
    add_features,
)


def test_clean_col_names():
    """
    clean_col_names doit :
      - retirer les espaces et caractères spéciaux
      - retirer les accents (car non A-Za-z)
      - conserver uniquement [A-Za-z0-9_]

    Exemple :
      - "Statut Marié(e)"   -> "StatutMarie"
        (l'espace et les caractères non ASCII sont retirés, le 'e' de "(e)" reste)
      - "heures_supplémentaires" -> "heures_supplmentaires"
        (le 'é' est retiré)
    """
    df = pd.DataFrame({"Statut Marié(e)": [1], "heures_supplémentaires": [0]})
    out = clean_col_names(df)

    assert list(out.columns) == ["StatutMarie", "heures_supplmentaires"]


def test_convert_binary_to_int():
    """
    convert_binary_to_int doit convertir une colonne contenant "Oui"/"Non"
    en 1/0 (int), en respectant la valeur positive passée en paramètre.
    """
    df = pd.DataFrame({"heure_supplementaires": ["Oui", "Non", "Oui", "Non"]})

    out = convert_binary_to_int(df, "heure_supplementaires", positive_value="Oui")

    # Résultat attendu : "Oui" -> 1, "Non" -> 0
    assert out["heure_supplementaires"].tolist() == [1, 0, 1, 0]
    # On peut aussi s'assurer que le type est bien entier
    assert out["heure_supplementaires"].dtype.kind in ("i", "u")  # int signé/non signé


def test_add_features_basic():
    """
    add_features doit ajouter au minimum :
      - ratio_revenu_poste = revenu_mensuel / (moyenne_poste + 1)
      - ratio_augmentation_promotion = augementation_salaire_precedente / (annees_depuis_la_derniere_promotion + 1)

    Ici on vérifie surtout la cohérence du ratio_augmentation_promotion
    avec des valeurs simples.
    """
    df = pd.DataFrame({
        "revenu_mensuel": [5000, 3000],
        "poste": ["Manager", "Consultant"],
        "augementation_salaire_precedente": [10, 5],
        "annees_depuis_la_derniere_promotion": [1, 0],
    })

    out = add_features(df)

    # Les deux colonnes calculées doivent exister
    assert {"ratio_revenu_poste", "ratio_augmentation_promotion"} <= set(out.columns)

    # Vérification du ratio_augmentation_promotion :
    # - ligne 0 : 10 / (1 + 1) = 10/2
    # - ligne 1 :  5 / (0 + 1) =  5/1
    assert out["ratio_augmentation_promotion"].tolist() == [10 / 2, 5 / 1]


def test_add_features_unknown_job():
    """
    Si le poste n'est pas connu dans les moyennes (MOYENNES_POSTE),
    la fonction utilise un +1 au dénominateur -> ratio_revenu_poste par défaut à 1.0
    (puisque map renvoie NaN, on a (revenu / (NaN + 1)) -> (revenu / NaN) ? Non,
    dans l'implémentation, on remplit avec 1.0 quand NaN via .fillna(1.0) après le calcul).
    """
    df = pd.DataFrame({
        "revenu_mensuel": [6000],
        "poste": ["Inconnu"],  # volontairement absent du mapping
        "augementation_salaire_precedente": [10],
        "annees_depuis_la_derniere_promotion": [0],
    })

    out = add_features(df)

    # Par convention dans l'implémentation : ratio_revenu_poste = 1.0 si poste inconnu
    assert out.loc[0, "ratio_revenu_poste"] == 1.0
