import pandas as pd
from futurisys_churn_api.api.preprocessing import (
    clean_col_names, 
    convert_binary_to_int, 
    add_features
)

def test_clean_col_names():
    """
    Teste si la fonction de nettoyage des noms de colonnes fonctionne correctement.
    """
    df = pd.DataFrame({"Statut Marié(e)": [1], "heures_supplémentaires": [0]})
    out = clean_col_names(df)
    assert list(out.columns) == ["StatutMarie", "heures_supplmentaires"]

def test_convert_binary_to_int():
    """
    Teste si la fonction de conversion binaire fonctionne correctement.
    """
    # Arrange: crée un DataFrame avec une colonne binaire
    df = pd.DataFrame({"heure_supplementaires": ["Oui", "Non", "Oui", "Non"]})
    out = convert_binary_to_int(df, "heure_supplementaires", positive_value="Oui")
    assert out["heure_supplementaires"].tolist() == [1, 0, 1, 0]

def test_add_features_basic():
    import pandas as pd
    df = pd.DataFrame({
        "revenu_mensuel": [5000, 3000],
        "poste": ["Manager", "Consultant"],
        "augementation_salaire_precedente": [10, 5],
        "annees_depuis_la_derniere_promotion": [1, 0],
    })
    out = add_features(df)
    assert {"ratio_revenu_poste", "ratio_augmentation_promotion"} <= set(out.columns)
    assert out["ratio_augmentation_promotion"].tolist() == [10/2, 5/1]

def test_add_features_unknown_job():
    import pandas as pd
    df = pd.DataFrame({
        "revenu_mensuel": [6000],
        "poste": ["Inconnu"],
        "augementation_salaire_precedente": [10],
        "annees_depuis_la_derniere_promotion": [0],
    })
    out = add_features(df)
    assert out.loc[0, "ratio_revenu_poste"] == 1.0