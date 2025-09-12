"""
But du test
-----------
Valider, sur un vrai dataset "brut", que le pipeline de prétraitement complet
(`convert_binary_to_int` → `add_features` → `encode_categorical`) fonctionne
de bout en bout sans erreur et produit des colonnes/valeurs conformes
aux attentes du modèle.

Stratégie
---------
1) On vérifie que le dataset fourni ressemble bien à des données brutes
   (certaines colonnes clés doivent être présentes) ; sinon on *skip* proprement.
2) On applique les trois étapes du préprocessing dans l’ordre.
3) On contrôle :
   - l’absence de NaN sur les features dérivées critiques,
   - la disparition des colonnes catégorielles "brutes" au profit de dummies,
   - le typage numérique des colonnes encodées ordinalement.
"""

import pytest
from futurisys_churn_api.api.preprocessing import (
    convert_binary_to_int,
    add_features,
    encode_categorical,
)

@pytest.mark.usefixtures("dataset_df")
def test_full_preprocessing_on_dataset(dataset_df):
    # Colonnes minimales attendues pour considérer le dataset comme "brut"
    required = {"revenu_mensuel", "annees_depuis_la_derniere_promotion", "poste"}
    if not required.issubset(set(dataset_df.columns)):
        pytest.skip(
            "Dataset fourni n'est pas brut "
            f"(colonnes manquantes: {sorted(required - set(dataset_df.columns))})"
        )

    # On travaille sur une copie pour éviter toute mutation du fixture
    df = dataset_df.copy()

    # Étape 1 — binarisation de valeurs oui/non et F/M
    df = convert_binary_to_int(df, "heure_supplementaires", positive_value="Oui")
    df = convert_binary_to_int(df, "genre", positive_value="F")

    # Étape 2 — création de features dérivées (ratios, etc.)
    df = add_features(df)

    # Étape 3 — encodage : dummies + ordinal pour certaines colonnes
    df = encode_categorical(df)

    # Assertions "métier" : les features dérivées ne doivent pas contenir de NaN
    assert not df["ratio_revenu_poste"].isna().any()
    assert not df["ratio_augmentation_promotion"].isna().any()

    # Les colonnes brutes catégorielles doivent avoir disparu (remplacées par dummies)
    for col in ["statut_marital", "domaine_etude", "departement"]:
        assert col not in df.columns

    # Les colonnes encodées ordinalement doivent être numériques
    assert df["poste"].dtype.kind in "if"  # int/float
    assert df["frequence_deplacement"].dtype.kind in "if"
