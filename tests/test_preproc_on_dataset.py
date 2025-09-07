import pytest
from futurisys_churn_api.api.preprocessing import convert_binary_to_int, add_features, encode_categorical

@pytest.mark.usefixtures("dataset_df")
def test_full_preprocessing_on_dataset(dataset_df):
    required = {"revenu_mensuel", "annees_depuis_la_derniere_promotion", "poste"}
    if not required.issubset(set(dataset_df.columns)):
        pytest.skip(f"Dataset fourni n'est pas brut (colonnes manquantes: {sorted(required - set(dataset_df.columns))})")

    df = dataset_df.copy()
    df = convert_binary_to_int(df, "heure_supplementaires", positive_value="Oui")
    df = convert_binary_to_int(df, "genre", positive_value="F")
    df = add_features(df)
    df = encode_categorical(df)

    assert not df["ratio_revenu_poste"].isna().any()
    assert not df["ratio_augmentation_promotion"].isna().any()
    for col in ["statut_marital", "domaine_etude", "departement"]:
        assert col not in df.columns
    assert df["poste"].dtype.kind in "if"
    assert df["frequence_deplacement"].dtype.kind in "if"
