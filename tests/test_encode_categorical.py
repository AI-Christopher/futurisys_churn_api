# tests/test_encode_categorical.py
import pandas as pd
import numpy as np
from futurisys_churn_api.api.preprocessing import (
    encode_categorical, clean_col_names, MAPPING_POSTE, MAPPING_FREQ
)

def _expected_dummy_names(prefix: str, values: list[str]) -> list[str]:
    raw = [f"{prefix}_{v}" for v in values]
    df_cols = pd.DataFrame(columns=raw)
    return list(clean_col_names(df_cols).columns)

def test_encode_categorical_basic():
    df_in = pd.DataFrame({
        "statut_marital": ["Célibataire", "Marié(e)"],
        "domaine_etude": ["Infra & Cloud", "Marketing"],
        "departement": ["Ressources Humaines", "Commercial"],
        "poste": ["Manager", "Consultant"],
        "frequence_deplacement": ["Fréquent", "Occasionnel"],
    })
    df_orig = df_in.copy(deep=True)

    out = encode_categorical(df_in)

    pd.testing.assert_frame_equal(df_in, df_orig)  # pas de mutation
    for col in ["statut_marital", "domaine_etude", "departement"]:
        assert col not in out.columns

    expected_statut = _expected_dummy_names("statut_marital", ["Célibataire", "Marié(e)"])
    expected_dom    = _expected_dummy_names("domaine_etude", ["Infra & Cloud", "Marketing"])
    expected_dept   = _expected_dummy_names("departement", ["Ressources Humaines", "Commercial"])
    for c in expected_statut + expected_dom + expected_dept:
        assert c in out.columns

    assert out.loc[0, "poste"] == MAPPING_POSTE["Manager"]
    assert out.loc[1, "poste"] == MAPPING_POSTE["Consultant"]
    assert out.loc[0, "frequence_deplacement"] == MAPPING_FREQ["Fréquent"]
    assert out.loc[1, "frequence_deplacement"] == MAPPING_FREQ["Occasionnel"]
    assert np.issubdtype(out["poste"].dtype, np.number)
    assert np.issubdtype(out["frequence_deplacement"].dtype, np.number)

def test_encode_categorical_unknown_values_become_nan():
    df = pd.DataFrame({
        "statut_marital": ["Célibataire"],
        "domaine_etude": ["Marketing"],
        "departement": ["Commercial"],
        "poste": ["Inconnu"],                 # hors mapping
        "frequence_deplacement": ["Bizarre"], # hors mapping
    })
    out = encode_categorical(df)
    assert pd.isna(out.loc[0, "poste"])
    assert pd.isna(out.loc[0, "frequence_deplacement"])
