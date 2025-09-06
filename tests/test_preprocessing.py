import pandas as pd
from futurisys_churn_api.api.preprocessing import clean_col_names, convert_binary_to_int

def test_clean_col_names():
    """
    Teste si la fonction de nettoyage des noms de colonnes fonctionne correctement.
    """
    df = pd.DataFrame({"Statut Marié(e)": [1], "heures_supplémentaires": [0]})
    out = clean_col_names(df)
    assert list(out.columns) == ["StatutMariee", "heures_supplementaires"]

def test_convert_binary_to_int():
    """
    Teste si la fonction de conversion binaire fonctionne correctement.
    """
    # Arrange: crée un DataFrame avec une colonne binaire
    df = pd.DataFrame({"heure_supplementaires": ["Oui", "Non", "Oui", "Non"]})
    out = convert_binary_to_int(df, "heure_supplementaires", positive_value="Oui")
    assert out["heure_supplementaires"].tolist() == [1, 0, 1, 0]