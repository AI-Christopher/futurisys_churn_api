import pandas as pd
import pytest
from futurisys_churn_api.api.preprocessing import add_features

def test_add_features_missing_columns_raises():
    df = pd.DataFrame({"revenu_mensuel": [1000], "poste": ["Manager"]})
    with pytest.raises(ValueError):
        add_features(df)  # manque deux colonnes -> lève ValueError
